# API 参考

## 核心服务

### SearchService

搜索服务，提供全文检索功能。

```python
from telegram_search.search import SearchService
from telegram_search.config import load_config

config = load_config()
service = SearchService(config)

# 执行搜索
result = service.search(
    query="关键词",
    limit=20,
    offset=0
)

# 返回结构
{
    "hits": [...],
    "estimatedTotalHits": 100,
    "processingTimeMs": 5
}
```

#### 方法

| 方法 | 参数 | 返回 |
|------|------|------|
| `search(query, limit, offset)` | 查询词、数量、偏移 | 搜索结果 |
| `close()` | - | 关闭连接 |

### IngestService

消息入库服务。

```python
from telegram_search.indexer import IngestService, IngestResult

service = IngestService(meili_client, message_filter)

# 单条入库
result = service.ingest_message(msg_dict)
# IngestResult.INDEXED / SKIPPED / ERROR

# 批量入库
service.ingest_batch(messages, raise_on_error=False)
```

### StatsService

统计服务。

```python
from telegram_search.stats import StatsService

service = StatsService(redis_config)

# 记录搜索
service.record_search("关键词")

# 获取统计
stats = service.get_stats()
# {"total_searches": 100, "top_keywords": [("词1", 50), ...]}
```

## 数据模型

### Message

消息文档结构（存入 Meilisearch）：

```python
{
    "id": "channel_msgid",      # 唯一标识
    "msg_id": 12345,            # 消息 ID
    "chat_id": -1001234567890,  # 频道 ID
    "chat_title": "频道名",      # 频道标题
    "text": "消息内容",          # 原始文本
    "tokens": ["分词", "结果"],  # 分词结果
    "date": 1704067200,         # Unix 时间戳
    "url": "https://t.me/..."   # 消息链接
}
```

### Channel

频道配置结构：

```python
{
    "channel_id": -1001234567890,
    "username": "channel_name",
    "title": "频道标题",
    "enabled": True
}
```
