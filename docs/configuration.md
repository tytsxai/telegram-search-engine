# 配置指南

## 配置文件

系统使用 TOML 格式配置文件，默认路径 `configs/app.toml`。

## 配置优先级

环境变量 > 配置文件 > 默认值

## Telegram 配置

```toml
[telegram]
bot_token = ""      # Bot Token (从 @BotFather 获取)
api_id = 0          # API ID (从 my.telegram.org 获取)
api_hash = ""       # API Hash
```

| 环境变量 | 说明 |
|---------|------|
| `TELEGRAM_BOT_TOKEN` | Bot Token |
| `TELEGRAM_API_ID` | API ID (整数) |
| `TELEGRAM_API_HASH` | API Hash |

## Meilisearch 配置

```toml
[meilisearch]
host = "http://localhost:7700"
api_key = ""
index_name = "telegram_messages"
timeout = 5
max_retries = 3
```

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `MEILI_HOST` | 服务地址 | `http://localhost:7700` |
| `MEILI_MASTER_KEY` | Master Key | - |
| `MEILI_INDEX` | 索引名称 | `telegram_messages` |
| `MEILI_TIMEOUT` | 超时秒数 | `5` |
| `MEILI_MAX_RETRIES` | 最大重试 | `3` |

## Redis 配置

```toml
[redis]
host = "localhost"
port = 6379
db = 0
cache_ttl = 3600
socket_timeout = 5
socket_connect_timeout = 5
max_retries = 3
```

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `REDIS_HOST` | 主机地址 | `localhost` |
| `REDIS_PORT` | 端口 | `6379` |
| `REDIS_DB` | 数据库编号 | `0` |
| `REDIS_CACHE_TTL` | 缓存过期(秒) | `3600` |
| `REDIS_SOCKET_TIMEOUT` | Socket 超时 | `5` |
| `REDIS_CONNECT_TIMEOUT` | 连接超时 | `5` |
| `REDIS_MAX_RETRIES` | 最大重试 | `3` |

## 搜索配置

```toml
[search]
default_limit = 20
max_limit = 100
```

## 索引器配置

```toml
[indexer]
batch_size = 100
rate_limit_delay = 1.0
state_flush_interval = 1.0
```

| 参数 | 说明 |
|------|------|
| `batch_size` | 批量入库大小 |
| `rate_limit_delay` | API 调用间隔(秒) |
| `state_flush_interval` | 状态刷新间隔(秒) |

## 频道配置

频道列表保存在 `configs/channels.json`：

```json
[
  {
    "channel_id": -1001234567890,
    "username": "example_channel",
    "title": "示例频道",
    "enabled": true
  }
]
```

使用 CLI 管理：

```bash
# 添加频道
python -m apps.crawler.channels add -1001234567890 --username example --title "示例"

# 列出频道
python -m apps.crawler.channels list

# 移除频道
python -m apps.crawler.channels remove -1001234567890
```

## 完整示例

`.env` 文件：

```bash
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
MEILI_MASTER_KEY=your_master_key
```
