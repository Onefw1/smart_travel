# 部署配置

- `docker/`：后续需要容器部署时放置 Dockerfile、Compose 等配置；当前不要求使用容器。
- `env/`：后续放置无真实凭据的 `.env.example` 配置样例。

应用初始化后再添加实际配置。部署操作说明放在 `docs/deployment/`；环境密钥写入本地 `.env`，不提交到 Git。
