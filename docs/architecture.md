# 系统架构

## 概述

Telegram 搜索引擎采用分层架构设计，将消息采集、文本处理、索引存储、搜索服务分离，便于独立扩展和维护。

## 架构图

```
                              ┌─────────────────────────────────────┐
                              │           Telegram API              │
                              └──────────────┬──────────────────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    │                        │                        │
           ┌────────▼────────┐      ┌────────▼────────┐      ┌────────▼────────┐
           │  RealtimeListener│      │  HistoricalSync │      │   Telegram Bot  │
           │   (实时监听)      │      │   (历史同步)     │      │   (用户交互)    │
           └────────┬────────┘      └────────┬────────┘      └────────┬────────┘
                    │                        │                        │
                    └────────────┬───────────┘                        │
                                 │                                    │
                    ┌────────────▼────────────┐                       │
                    │      IngestService      │                       │
                    │       (入库服务)         │                       │
                    └────────────┬────────────┘                       │
                                 │                                    │
                    ┌────────────▼────────────┐                       │
                    │        Pipeline         │                       │
                    │  ┌──────────────────┐   │                       │
                    │  │   MessageFilter  │   │                       │
                    │  │   (消息过滤)      │   │                       │
                    │  └────────┬─────────┘   │                       │
                    │  ┌────────▼─────────┐   │                       │
                    │  │   Normalizer     │   │                       │
                    │  │   (文本规范化)    │   │                       │
                    │  └────────┬─────────┘   │                       │
                    │  ┌────────▼─────────┐   │                       │
                    │  │   Tokenizer      │   │                       │
                    │  │   (中文分词)      │   │                       │
                    │  └────────┬─────────┘   │                       │
                    │  ┌────────▼─────────┐   │                       │
                    │  │   Deduper        │   │                       │
                    │  │   (SimHash去重)   │   │                       │
                    │  └──────────────────┘   │                       │
                    └────────────┬────────────┘                       │
                                 │                                    │
                    ┌────────────▼────────────┐          ┌────────────▼────────────┐
                    │      MeiliClient        │◀─────────│     SearchService       │
                    │     (Meilisearch)       │          │      (搜索服务)          │
                    └─────────────────────────┘          └────────────┬────────────┘
                                                                      │
                                                         ┌────────────▼────────────┐
                                                         │      CacheManager       │
                                                         │        (Redis)          │
                                                         └─────────────────────────┘
```

## 核心模块

### 1. 采集层 (Indexer)

| 模块 | 文件 | 职责 |
|------|------|------|
| TelethonCrawler | `indexer/telethon_client.py` | Telegram 客户端封装 |
| RealtimeListener | `indexer/realtime_listener.py` | 实时消息监听 |
| HistoricalSync | `indexer/historical_sync.py` | 历史消息同步 |
| IngestService | `indexer/ingest_service.py` | 消息入库协调 |
| ChannelRegistry | `indexer/channel_registry.py` | 频道配置管理 |
| StateStore | `indexer/state_store.py` | 同步进度持久化 |

### 2. 处理管道 (Pipeline)

| 模块 | 文件 | 职责 |
|------|------|------|
| MessageFilter | `pipeline/filters.py` | 消息过滤（空消息、系统消息） |
| Normalizer | `pipeline/normalizer.py` | 文本规范化（繁简转换） |
| Tokenizer | `pipeline/tokenizer.py` | jieba 中文分词 |
| Deduper | `pipeline/deduper.py` | SimHash 近似去重 |
| Transformer | `pipeline/transformer.py` | 字段转换与映射 |

### 3. 搜索层 (Search)

| 模块 | 文件 | 职责 |
|------|------|------|
| MeiliClient | `search/meili_client.py` | Meilisearch 客户端 |
| SearchService | `search/search_service.py` | 搜索业务逻辑 |
| QueryParser | `search/query_parser.py` | 查询解析与优化 |

### 4. 缓存层 (Cache)

| 模块 | 文件 | 职责 |
|------|------|------|
| CacheManager | `cache/manager.py` | Redis 缓存管理 |
| CacheKey | `cache/keys.py` | 缓存键生成策略 |

### 5. 统计层 (Stats)

| 模块 | 文件 | 职责 |
|------|------|------|
| StatsService | `stats/service.py` | 搜索统计服务 |

## 数据流

### 消息采集流程

```
1. Telegram Channel 发布消息
2. RealtimeListener 接收事件 / HistoricalSync 拉取历史
3. IngestService 接收原始消息
4. Pipeline 处理：
   - MessageFilter: 过滤无效消息
   - Normalizer: 繁简转换、Unicode 规范化
   - Tokenizer: jieba 分词生成 tokens
   - Deduper: SimHash 计算，过滤重复
5. MeiliClient 批量写入索引
6. StateStore 更新同步进度
```

### 搜索流程

```
1. 用户通过 Bot 发送 /search 命令
2. SearchService 接收查询
3. CacheManager 检查缓存
4. 缓存未命中：
   - QueryParser 解析查询
   - MeiliClient 执行搜索
   - 结果写入缓存
5. 返回格式化结果给用户
6. StatsService 记录搜索统计
```

## 技术选型

| 组件 | 技术 | 理由 |
|------|------|------|
| 消息采集 | Telethon | 功能完整的 Telegram MTProto 客户端 |
| Bot 框架 | python-telegram-bot | 官方推荐，异步支持好 |
| 全文搜索 | Meilisearch | 轻量、快速、中文支持好 |
| 缓存 | Redis | 高性能、支持多种数据结构 |
| 中文分词 | jieba | 成熟稳定、词库丰富 |
| 繁简转换 | OpenCC | 准确率高 |
| 去重算法 | SimHash | 适合短文本近似去重 |
| 配置管理 | Pydantic | 类型安全、环境变量支持 |
