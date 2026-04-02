"""Telegram Bot for search interface."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.helpers import escape_markdown
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from telegram_search.config import AppConfig, load_config
from telegram_search.search import SearchService
from telegram_search.stats import StatsService
from telegram_search.logging import setup_logging, get_logger, safe_error
from telegram_search.runtime import check_optional_redis, bootstrap_search_backend, validate_runtime_config

logger = get_logger(__name__)

PAGE_SIZE = 5


@dataclass
class AppServices:
    """Holds initialized application services."""

    search: SearchService
    stats: StatsService


_services: AppServices | None = None


def init_services(config: AppConfig) -> AppServices:
    """Initialize application services once. Call from main()."""
    global _services
    _services = AppServices(
        search=SearchService(config),
        stats=StatsService(config.redis),
    )
    return _services


def get_services() -> AppServices:
    """Get initialized services. Raises if not yet initialized."""
    if _services is None:
        raise RuntimeError("Services not initialized. Call init_services() first.")
    return _services


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    await update.message.reply_text("欢迎使用 Telegram 搜索引擎!\n使用 /search <关键词> 进行搜索")


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /search command."""
    if not context.args:
        await update.message.reply_text("请输入搜索关键词")
        return

    query = " ".join(context.args)
    context.user_data["query"] = query
    context.user_data["page"] = 0

    await do_search(update, context)


async def do_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Execute search with pagination."""
    query = context.user_data.get("query", "")
    page = context.user_data.get("page", 0)
    services = get_services()

    if page == 0:
        try:
            services.stats.record_search(query)
        except Exception as e:
            logger.error("stats_error", **safe_error(e))

    try:
        result = await asyncio.to_thread(
            services.search.search, query, limit=PAGE_SIZE, offset=page * PAGE_SIZE
        )
        hits = result.get("hits", [])

        if not hits:
            text = "未找到相关结果"
            if update.callback_query:
                await update.callback_query.answer(text)
            else:
                await update.message.reply_text(text)
            return

        response = format_results(hits)
        keyboard = build_pagination_keyboard(result, page)

        if update.callback_query:
            await update.callback_query.edit_message_text(
                response, parse_mode="Markdown", reply_markup=keyboard
            )
        else:
            await update.message.reply_text(response, parse_mode="Markdown", reply_markup=keyboard)
    except Exception as e:
        logger.error("search_error", **safe_error(e))
        text = "搜索出错，请稍后重试"
        if update.callback_query:
            await update.callback_query.answer(text)
        else:
            await update.message.reply_text(text)


def format_results(hits: list[dict[str, Any]]) -> str:
    """Format search results for Telegram."""
    lines = []
    for hit in hits[:PAGE_SIZE]:
        title = escape_markdown(hit.get("chat_title", "未知来源"), version=1)
        text = escape_markdown(hit.get("text", "")[:100], version=1)
        url = hit.get("url", "")
        lines.append(f"*{title}*\n{text}...")
        if url:
            lines.append(f"[查看原文]({url})")
        lines.append("")
    return "\n".join(lines)


def _result_total_hits(result: dict[str, Any]) -> int:
    """Read total hits from Meilisearch-compatible result metadata."""
    for key in ("estimatedTotalHits", "totalHits", "nbHits"):
        value = result.get(key)
        if isinstance(value, int) and value >= 0:
            return value
    hits = result.get("hits", [])
    return len(hits) if isinstance(hits, list) else 0


def build_pagination_keyboard(
    result: dict[str, Any],
    page: int,
) -> InlineKeyboardMarkup | None:
    """Build pagination keyboard."""
    hits = result.get("hits", [])
    hits_count = len(hits) if isinstance(hits, list) else 0
    has_next_page = (page * PAGE_SIZE) + hits_count < _result_total_hits(result)
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton("⬅️ 上一页", callback_data="prev"))
    if has_next_page:
        buttons.append(InlineKeyboardButton("下一页 ➡️", callback_data="next"))
    return InlineKeyboardMarkup([buttons]) if buttons else None


async def pagination_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle pagination button clicks."""
    query = update.callback_query
    await query.answer()

    action = query.data
    page = context.user_data.get("page", 0)

    if action == "next":
        context.user_data["page"] = page + 1
    elif action == "prev" and page > 0:
        context.user_data["page"] = page - 1

    await do_search(update, context)


async def suggest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /suggest command."""
    if not context.args:
        await update.message.reply_text("请输入关键词获取建议")
        return

    query = " ".join(context.args)
    await update.message.reply_text(f"搜索建议: {query}\n提示: 使用 /search {query} 进行搜索")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stats command."""
    services = get_services()

    try:
        data = services.stats.get_stats()
        total = data.get("total_searches", 0)
        keywords = data.get("top_keywords", [])

        lines = ["📊 **搜索统计**", f"总搜索次数: {total}", ""]

        if keywords:
            lines.append("🔥 **热门关键词**")
            for i, (kw, count) in enumerate(keywords, 1):
                lines.append(f"{i}. {kw} ({int(count)})")
        else:
            lines.append("暂无热门关键词数据")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        logger.error("stats_cmd_error", **safe_error(e))
        await update.message.reply_text("获取统计信息失败")


def main() -> None:
    """Run the bot."""
    config = load_config()
    setup_logging(config.debug)
    validate_runtime_config(config, component="bot")
    bootstrap_search_backend(config)
    check_optional_redis(config)

    services = init_services(config)

    app = Application.builder().token(config.telegram.bot_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CommandHandler("suggest", suggest))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(pagination_callback))

    logger.info("bot_starting")
    try:
        app.run_polling()
    finally:
        services.search.close()
        services.stats.close()
        logger.info("bot_shutdown")


if __name__ == "__main__":
    main()
