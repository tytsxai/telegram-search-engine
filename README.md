# Telegram Search Engine（tg-search-engine）

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Meilisearch](https://img.shields.io/badge/Meilisearch-1.6+-purple.svg)](https://www.meilisearch.com/)
[![Redis](https://img.shields.io/badge/Redis-7+-red.svg)](https://redis.io/)

> **Telegram channel crawler + full-text search** — Telethon 采集、Meilisearch 检索、中文 NLP（jieba / 拼音 / 繁简）、Redis 缓存、Bot 搜索入口。

[English](#english) | [中文](#中文)

- 仓库：https://github.com/tytsxai/tg-search-engine
- 采集入口：`python -m apps.crawler.main`
- Bot 入口：`python -m apps.bot.main`
- License：MIT

---

## English

Self-hosted high-performance **Telegram channel message crawler and full-text search engine** with a Chinese NLP pipeline.

### Who it is for

Operators indexing public channel text for search; developers needing Meilisearch + Telethon reference architecture; teams that want a Telegram Bot search UI.

### Highlights

- **Fast search** — Meilisearch-backed full-text retrieval
- **Chinese optimized** — jieba tokenization, pinyin index, Traditional/Simplified conversion
- **Real-time + historical** — live monitoring and batch historical sync
- **Near-duplicate filter** — SimHash
- **Bot interface** — `/search`, `/suggest`, `/stats`
- **Redis cache** — hot query acceleration

### Limits (honest)

- Requires your own Telegram API credentials, Meilisearch, and Redis
- First Telethon run needs interactive phone verification for session init
- Performance claims depend on hardware, index size, and query patterns — validate in your environment
- Only indexes content your account is allowed to access; respect Telegram ToS and copyright

---

## 中文

自托管的 **Telegram 频道消息采集 + 全文搜索** 系统：Telethon 拉取、管道清洗、Meilisearch 建索引、Redis 缓存、Bot 查询。

### 项目是什么 / 解决什么问题

频道历史难搜、多频道信息分散。本项目把消息同步进搜索引擎，支持中文分词与拼音，并在 Telegram Bot 内直接检索。

### 适合谁

| 角色 | 场景 |
|------|------|
| 运营 / 情报整理 | 自建频道内容检索 |
| 开发者 | Meilisearch + 中文管道参考 |
| 运维 | Docker Compose 双服务（crawler + bot） |

### 为什么选择这个项目？

| 特性 | 说明 |
|------|------|
| 🚀 **Meilisearch 全文检索** | 面向消息文本的快速检索（耗时取决于数据规模与部署） |
| 🇨🇳 **中文深度优化** | jieba 分词 + 拼音索引 + 繁简转换 |
| 🔄 **实时 + 历史** | 双模式采集 |
| 🧹 **智能去重** | SimHash 近似匹配 |
| 💾 **缓存加速** | Redis 热点缓存 |
| 🤖 **Bot 入口** | `/search` 等命令直接搜 |

## 功能特性

- **消息采集**：实时监听 + 历史同步，多频道配置
- **全文检索**：Meilisearch
- **中文优化**：jieba、拼音、繁简（OpenCC）
- **近似去重**：SimHash
- **缓存加速**：Redis
- **搜索统计**：热门关键词等
- **Bot 交互**：Telegram Bot 搜索界面

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
git clone https://github.com/tytsxai/tg-search-engine.git
cd tg-search-engine
```

### 2. 启动依赖服务

```bash
docker compose up -d
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入你的 API 凭证

# 生产环境可直接从模板生成
cp .env.production.example .env.production
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
make quality
```

## 注意事项

- 历史同步进度保存于 `state.json`，生产环境应挂载持久化卷
- 批量入库大小由 `indexer.batch_size` 控制（默认 100）
- 采集器支持优雅关闭（Ctrl+C）
- 首次运行 Telethon 需要手机验证；生产环境需先交互式完成一次 session 初始化

## 生产部署

- 使用 `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`
- 生产环境必须设置 `APP_ENV=production`、`MEILI_MASTER_KEY`、`REDIS_PASSWORD`
- `crawler` 容器默认以 `--mode both` 启动，先补历史缺口再进入实时监听
- 采集器需持久化 `/data`，保存 `state.json`、`channels.json` 与 Telethon session
- 上线前建议先执行 `make health-bot`、`make health-crawler`
- 详细步骤见 [docs/deployment.md](docs/deployment.md) 和 [docs/operations.md](docs/operations.md)

## License

MIT

## Contributing

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 使用场景

- 多频道内容统一检索
- 运营复盘：按关键词找历史帖
- 自建「站内搜」替代手工翻频道

## 限制与注意事项（补充）

- 历史进度在 `state.json`，生产务必持久化
- 仅处理你有权访问的频道内容；勿用于未授权抓取
- 中文管道与去重会带来 CPU 成本，大库需自行压测
- 「毫秒级」取决于 Meilisearch 与机器配置，非绝对 SLA

## SEO / 检索关键词

Telegram 搜索引擎, Telegram full-text search, Meilisearch Telegram, Telethon crawler, jieba 拼音搜索, 频道消息检索, self-hosted Telegram search engine

## Acknowledgments

- [Meilisearch](https://www.meilisearch.com/)
- [Telethon](https://github.com/LonamiWebs/Telethon)
- [jieba](https://github.com/fxsjy/jieba)
- [OpenCC](https://github.com/BYVoid/OpenCC)
