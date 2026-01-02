# Telegram 搜索引擎

面向 Telegram 频道消息的采集与搜索系统，内置中文处理管道（分词、拼音、繁简转换）与缓存加速。

## 功能概览

- 频道消息采集：实时监听 + 历史同步
- Meilisearch 全文检索
- Redis 缓存与搜索统计
- 中文文本处理与近似去重

## 运行环境

- Python 3.11+
- Redis
- Meilisearch
- Telegram API ID / Hash 与 Bot Token

## 配置

默认读取 `configs/app.toml`，也支持环境变量覆盖：

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_API_ID`
- `TELEGRAM_API_HASH`
- `MEILI_HOST`
- `MEILI_MASTER_KEY`
- `MEILI_INDEX`
- `MEILI_TIMEOUT`
- `MEILI_MAX_RETRIES`
- `REDIS_HOST`
- `REDIS_PORT`
- `REDIS_DB`
- `REDIS_CACHE_TTL`
- `REDIS_SOCKET_TIMEOUT`
- `REDIS_CONNECT_TIMEOUT`
- `REDIS_MAX_RETRIES`

频道列表保存在 `configs/channels.json`。

## 常用命令

安装依赖（推荐虚拟环境）：

```bash
pip install -e ".[dev]"
```

管理频道：

```bash
python -m apps.crawler.channels add <channel_id> --username <username> --title <title>
python -m apps.crawler.channels remove <channel_id>
python -m apps.crawler.channels list
```

运行采集器：

```bash
python -m apps.crawler.main --mode historical --limit 1000
python -m apps.crawler.main --mode realtime
python -m apps.crawler.main --mode both --limit 1000
```

运行 Bot：

```bash
python -m apps.bot.main
```

运行测试：

```bash
pytest
```

## 备注

- 历史同步进度保存于 `state.json`（可在配置中调整刷新频率）。
- 批量入库大小由 `indexer.batch_size` 控制。
