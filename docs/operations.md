# 运维手册

## 日常检查

每天至少确认：

- `docker compose ... ps` 中 `bot`、`crawler`、`meilisearch`、`redis` 全部为 `healthy`
- Bot `/search` 可用
- `crawler` 日志持续有同步或监听活动
- Meilisearch 与 Redis 数据目录容量正常

## 告警基线

现阶段不引入独立监控系统，最小可用告警建议如下：

- 任一容器状态变为 `unhealthy`
- 任一容器持续重启
- 日志出现 `healthcheck_failed`
- 日志出现 `crawler_error`
- 日志出现 `meili_request_failed`
- 日志出现连续 `telegram_flood_wait`

## 备份

至少备份三类数据：

1. 搜索索引
2. 缓存/统计
3. crawler 本地状态

### Meilisearch

```bash
curl -X POST -H "Authorization: Bearer ${MEILI_MASTER_KEY}" \
  http://localhost:7700/snapshots
```

### Redis

```bash
redis-cli -a "${REDIS_PASSWORD}" BGSAVE
```

### Crawler 状态

备份持久化卷中的：

- `/data/state.json`
- `/data/channels.json`
- `/data/telegram/session.session`

## 恢复

### 恢复 crawler 状态

先停 crawler，再恢复以下文件：

- `/data/state.json`
- `/data/channels.json`
- `/data/telegram/session.session`

恢复后再启动 crawler，避免重新全量扫历史或要求重新登录 Telegram。

### 恢复 Meilisearch

- 恢复 Meilisearch 数据卷，或
- 使用 snapshot 恢复后再启动 bot/crawler

### 恢复 Redis

Redis 丢失不会导致核心搜索数据丢失，但会丢：

- 搜索缓存
- 搜索统计

这属于可接受降级，不应阻塞搜索服务恢复。

## 发布流程

1. 先构建并启动新镜像到测试环境。
2. 执行 `python -m telegram_search.health --component bot`。
3. 执行 `python -m telegram_search.health --component crawler`。
4. 手工验证 `/search`。
5. 确认 crawler 可读取已有 session 与 state。
6. 确认 crawler 重启后会先补齐停机期间缺口，再恢复实时监听。
7. 再滚动替换生产实例。

## 回滚

回滚原则：先回镜像，再决定是否回数据。

1. 切回上一版 bot / crawler 镜像。
2. 保留当前 `/data`、Meilisearch、Redis 数据卷。
3. 如果新版本写入了不兼容索引设置，再恢复最近一次 Meilisearch snapshot。

不要先删数据卷。这个项目当前没有复杂迁移，优先做镜像回退。

## 常见故障

### crawler 启动失败并提示 session 缺失

原因：生产环境无 TTY，且没有预先完成 Telethon 登录。

处理：按 [deployment.md](deployment.md) 里的“初始化 Telethon Session”先做一次交互式启动。

### 搜索命中为空但 crawler 正常

先查：

- Meilisearch 索引是否存在
- `configs/meilisearch.json` 是否已应用
- `crawler` 是否有 `batch_ingest_error`

### Bot 可用但统计一直为 0

通常是 Redis 不可达或密码错误。搜索仍可继续，但缓存和统计会降级。
