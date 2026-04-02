# Telegram Search Engine

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Meilisearch](https://img.shields.io/badge/Meilisearch-1.6+-purple.svg)](https://www.meilisearch.com/)
[![Redis](https://img.shields.io/badge/Redis-7+-red.svg)](https://redis.io/)

[English](#english) | [中文](#中文)

---

## English

High-performance Telegram channel message crawler and full-text search engine with built-in Chinese NLP pipeline.

### Highlights

- **⚡ Blazing Fast** - Millisecond search response powered by Meilisearch
- **🇨🇳 Chinese Optimized** - jieba tokenization, pinyin index, Traditional/Simplified conversion
- **🔄 Real-time Sync** - Live message monitoring + historical batch sync
- **🧹 Smart Dedup** - SimHash algorithm filters near-duplicate content
- **🤖 Bot Interface** - Search directly via Telegram Bot
- **📊 Analytics** - Track popular keywords and search trends

---

## 中文

高性能 Telegram 频道消息采集与全文搜索系统，内置中文处理管道（分词、拼音、繁简转换）与缓存加速。

### 为什么选择这个项目？

| 特性 | 说明 |
|------|------|
| 🚀 **毫秒级搜索** | Meilisearch 驱动，支持百万级消息即时检索 |
| 🇨🇳 **中文深度优化** | jieba 分词 + 拼音索引 + 繁简转换，搜索更精准 |
| 🔄 **实时 + 历史** | 双模式采集，不漏掉任何消息 |
| 🧹 **智能去重** | SimHash 近似匹配，过滤转发和重复内容 |
| 💾 **缓存加速** | Redis 热点缓存，高并发无压力 |
| 🤖 **开箱即用** | Telegram Bot 直接搜索，无需额外部署 |

## 功能特性

- **消息采集**：实时监听 + 历史同步，支持多频道并行
- **全文检索**：基于 Meilisearch，毫秒级响应
- **中文优化**：jieba 分词、拼音索引、繁简转换
- **近似去重**：SimHash 算法过滤重复内容
- **缓存加速**：Redis 缓存热点查询
- **搜索统计**：热门关键词、搜索次数统计
- **Bot 交互**：Telegram Bot 提供搜索界面

## 系统架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Telegram   │────▶│   Crawler   │────▶│  Pipeline   │
│  Channels   │     │  (Telethon) │     │  (Filter/   │
└─────────────┘     └─────────────┘     │  Transform) │
                                        └──────┬──────┘
                                               │
┌─────────────┐     ┌─────────────┐     ┌──────▼──────┐
│  Telegram   │◀────│  Search     │◀────│ Meilisearch │
│    Bot      │     │  Service    │     │   Index     │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                    ┌──────▼──────┐
                    │    Redis    │
                    │   (Cache)   │
                    └─────────────┘
```

## 运行环境

- Python 3.11+
- Redis 7+
- Meilisearch 1.6+
- Telegram API ID / Hash（从 https://my.telegram.org 获取）
- Telegram Bot Token（从 @BotFather 获取）

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/tytsxai/telegram-search-engine.git
cd telegram-search-engine
```

### 2. 启动依赖服务

```bash
docker compose up -d
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入你的 API 凭证
```

### 4. 安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

### 5. 配置频道

```bash
python -m apps.crawler.channels add -1001234567890 --username <username> --title <title>
```

### 6. 运行采集器

```bash
# 历史同步
python -m apps.crawler.main --mode historical --limit 1000

# 实时监听
python -m apps.crawler.main --mode realtime

# 两者同时
python -m apps.crawler.main --mode both --limit 1000
```

### 7. 启动 Bot

```bash
python -m apps.bot.main
```

## 配置说明

默认读取 `configs/app.toml`，支持环境变量覆盖：

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `TELEGRAM_BOT_TOKEN` | Bot Token | - |
| `TELEGRAM_API_ID` | API ID | - |
| `TELEGRAM_API_HASH` | API Hash | - |
| `TELEGRAM_SESSION_PATH` | Telethon Session 路径 | `session` |
| `APP_ENV` | 运行环境 | `development` |
| `MEILI_HOST` | Meilisearch 地址 | `http://localhost:7700` |
| `MEILI_MASTER_KEY` | Meilisearch 密钥 | - |
| `MEILI_INDEX` | 索引名称 | `telegram_messages` |
| `MEILI_SETTINGS_PATH` | Meilisearch 索引设置文件 | `configs/meilisearch.json` |
| `REDIS_HOST` | Redis 地址 | `localhost` |
| `REDIS_PORT` | Redis 端口 | `6379` |
| `REDIS_PASSWORD` | Redis 密码 | - |
| `REDIS_CACHE_TTL` | 缓存过期时间(秒) | `3600` |
| `STATE_FILE_PATH` | 历史同步状态文件 | `state.json` |
| `CHANNELS_CONFIG_PATH` | 频道配置文件 | `configs/channels.json` |

完整配置项见 `configs/app.toml`。

## 项目结构

```
├── apps/
│   ├── bot/           # Telegram Bot 应用
│   │   └── main.py    # Bot 入口
│   └── crawler/       # 消息采集器
│       ├── main.py    # 采集器入口
│       └── channels.py # 频道管理 CLI
├── telegram_search/   # 核心库
│   ├── cache/         # Redis 缓存层
│   ├── indexer/       # 索引与采集
│   ├── models/        # 数据模型
│   ├── pipeline/      # 文本处理管道
│   ├── search/        # 搜索服务
│   └── stats/         # 统计服务
├── configs/           # 配置文件
├── tests/             # 测试用例
└── docker-compose.yml # Docker 编排
```

## Bot 命令

| 命令 | 说明 |
|------|------|
| `/start` | 显示欢迎信息 |
| `/search <关键词>` | 搜索消息 |
| `/suggest <关键词>` | 获取搜索建议 |
| `/stats` | 查看搜索统计 |

## 开发

### 运行测试

```bash
pytest
```

### 代码检查

```bash
ruff check .
mypy telegram_search
```

## 注意事项

- 历史同步进度保存于 `state.json`，生产环境应挂载持久化卷
- 批量入库大小由 `indexer.batch_size` 控制（默认 100）
- 采集器支持优雅关闭（Ctrl+C）
- 首次运行 Telethon 需要手机验证；生产环境需先交互式完成一次 session 初始化

## 生产部署

- 使用 `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`
- 生产环境必须设置 `APP_ENV=production`、`MEILI_MASTER_KEY`、`REDIS_PASSWORD`
- 采集器需持久化 `/data`，保存 `state.json`、`channels.json` 与 Telethon session
- 详细步骤见 [docs/deployment.md](docs/deployment.md) 和 [docs/operations.md](docs/operations.md)

## License

MIT

## Contributing

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## Star History

如果这个项目对你有帮助，请给一个 ⭐ Star！

## Acknowledgments

- [Meilisearch](https://www.meilisearch.com/) - 快速、相关性强的搜索引擎
- [Telethon](https://github.com/LonamiWebs/Telethon) - 优秀的 Telegram MTProto 客户端
- [jieba](https://github.com/fxsjy/jieba) - 中文分词利器
- [OpenCC](https://github.com/BYVoid/OpenCC) - 繁简转换工具
