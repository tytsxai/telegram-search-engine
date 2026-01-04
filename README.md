# Telegram 搜索引擎

高性能 Telegram 频道消息采集与全文搜索系统，内置中文处理管道（分词、拼音、繁简转换）与缓存加速。

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
git clone <repo-url>
cd telegram-search-engine
```

### 2. 启动依赖服务

```bash
docker-compose up -d
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入你的 API 凭证
```

### 4. 安装依赖

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 5. 配置频道

```bash
python -m apps.crawler.channels add <channel_id> --username <username> --title <title>
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
| `MEILI_HOST` | Meilisearch 地址 | `http://localhost:7700` |
| `MEILI_MASTER_KEY` | Meilisearch 密钥 | - |
| `MEILI_INDEX` | 索引名称 | `telegram_messages` |
| `REDIS_HOST` | Redis 地址 | `localhost` |
| `REDIS_PORT` | Redis 端口 | `6379` |
| `REDIS_CACHE_TTL` | 缓存过期时间(秒) | `3600` |

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

- 历史同步进度保存于 `state.json`
- 批量入库大小由 `indexer.batch_size` 控制（默认 100）
- 采集器支持优雅关闭（Ctrl+C）
- 首次运行 Telethon 需要手机验证

## License

MIT
