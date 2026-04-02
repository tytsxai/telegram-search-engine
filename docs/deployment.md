# 部署指南

## 目标

本文档对应当前仓库的可上线部署方式，不依赖额外编排系统，只覆盖：

- Meilisearch
- Redis
- Crawler
- Bot

## 生产前提

- Python 3.11+
- Docker Compose v2
- 已准备 `.env.production`
- 已为 crawler 预留持久化目录 `/data`
- 已获取 Telegram API ID / Hash 与 Bot Token

推荐直接从模板生成：

```bash
cp .env.production.example .env.production
```

## 必填环境变量

最少需要：

```bash
APP_ENV=production
TELEGRAM_BOT_TOKEN=
TELEGRAM_API_ID=
TELEGRAM_API_HASH=
MEILI_MASTER_KEY=
REDIS_PASSWORD=
```

推荐同时显式指定：

```bash
MEILI_HOST=http://meilisearch:7700
MEILI_INDEX=telegram_messages
TELEGRAM_SESSION_PATH=/data/telegram/session
STATE_FILE_PATH=/data/state.json
CHANNELS_CONFIG_PATH=/data/channels.json
MEILI_SETTINGS_PATH=configs/meilisearch.json
```

## 首次启动前

### 1. 配置频道

频道配置必须落到生产持久化路径，而不是容器临时文件系统：

```bash
export CHANNELS_CONFIG_PATH=/data/channels.json
python3 -m apps.crawler.channels add -1001234567890 --username example --title "Example"
```

### 2. 初始化 Telethon Session

`crawler` 首次运行需要交互式登录 Telegram。在线上无 TTY 服务里直接启动会失败，这是故意的保护，避免服务卡死在验证码输入。

先执行一次交互式启动：

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm crawler \
  python -m apps.crawler.main --mode historical --limit 1
```

登录完成后，确认持久化卷内存在：

- `/data/telegram/session.session`
- `/data/channels.json`

## 启动

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

说明：

- `crawler` 镜像默认使用 `python -m apps.crawler.main --mode both`
- 这会先按 `state.json` 做增量历史补齐，再进入实时监听，避免重启窗口丢消息

## 健康检查

容器内已内置健康检查：

- `bot`: `python -m telegram_search.health --component bot`
- `crawler`: `python -m telegram_search.health --component crawler`
- `meilisearch`: `GET /health`
- `redis`: `redis-cli ping`

手工验证：

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f bot crawler
```

## 启动后确认项

- `crawler` 日志出现 `crawler_initialized`
- `crawler` 日志先出现 `syncing_channel` 或 `channel_synced`，随后进入 `starting_realtime`
- `bot` 日志出现 `bot_starting`
- `healthcheck_ok` 周期性通过
- Meilisearch 索引已存在且已应用 `configs/meilisearch.json`
- 搜索命令可返回结果

## 关键部署约束

- `MEILI_MASTER_KEY` 在生产环境不能为空
- `REDIS_PASSWORD` 在生产环境不能为空
- `/data` 必须持久化，否则 crawler 重建后会丢失：
  - 历史同步进度
  - 已配置频道列表
  - Telethon session

## systemd 部署

如果不用 Docker，最少也要满足同样约束：

- 固定 `WorkingDirectory`
- 使用持久化 `TELEGRAM_SESSION_PATH`
- 使用持久化 `STATE_FILE_PATH`
- 启动前执行 `python -m telegram_search.health --component <bot|crawler>`
- `Restart=always`

## 失败时先查什么

- `healthcheck_failed`
- `meili_request_failed`
- `crawler_error`
- `search_error`
- `telegram_flood_wait`
