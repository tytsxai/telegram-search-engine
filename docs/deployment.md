# 部署指南

## Docker 部署

### 启动依赖服务

```bash
docker-compose up -d
```

服务包括：
- **Meilisearch**: 端口 7700
- **Redis**: 端口 6379

### 验证服务

```bash
# Meilisearch
curl http://localhost:7700/health

# Redis
redis-cli ping
```

## 生产环境配置

### Meilisearch

```yaml
# docker-compose.prod.yml
services:
  meilisearch:
    image: getmeili/meilisearch:v1.6
    environment:
      - MEILI_MASTER_KEY=${MEILI_MASTER_KEY}
      - MEILI_ENV=production
    volumes:
      - /data/meili:/meili_data
    restart: always
```

### Redis

```yaml
services:
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - /data/redis:/data
    restart: always
```

## 进程管理

### systemd 服务

Bot 服务 `/etc/systemd/system/telegram-bot.service`：

```ini
[Unit]
Description=Telegram Search Bot
After=network.target

[Service]
Type=simple
User=app
WorkingDirectory=/opt/telegram-search
ExecStart=/opt/telegram-search/.venv/bin/python -m apps.bot.main
Restart=always
EnvironmentFile=/opt/telegram-search/.env

[Install]
WantedBy=multi-user.target
```

采集器服务：

```ini
[Unit]
Description=Telegram Crawler
After=network.target

[Service]
Type=simple
User=app
WorkingDirectory=/opt/telegram-search
ExecStart=/opt/telegram-search/.venv/bin/python -m apps.crawler.main --mode realtime
Restart=always
EnvironmentFile=/opt/telegram-search/.env

[Install]
WantedBy=multi-user.target
```

启用服务：

```bash
sudo systemctl enable telegram-bot telegram-crawler
sudo systemctl start telegram-bot telegram-crawler
```

## 监控

### 日志

应用使用 structlog 输出 JSON 格式日志：

```bash
journalctl -u telegram-bot -f
```

### 健康检查

```bash
# Meilisearch 索引状态
curl http://localhost:7700/indexes/telegram_messages/stats

# Redis 连接
redis-cli info clients
```

## 备份

### Meilisearch 数据

```bash
# 创建快照
curl -X POST http://localhost:7700/snapshots

# 数据目录
/meili_data/data.ms/
```

### Redis 数据

```bash
# RDB 快照
redis-cli BGSAVE

# AOF 文件
/data/appendonly.aof
```

## 故障排查

| 问题 | 检查项 |
|------|--------|
| Bot 无响应 | Token 配置、网络连接 |
| 搜索无结果 | Meilisearch 索引状态 |
| 采集器断开 | API 凭证、Session 文件 |
| 缓存失效 | Redis 连接、TTL 配置 |
