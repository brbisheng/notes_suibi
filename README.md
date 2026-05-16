# Suibi MVP

## 1) 环境准备

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## 2) 初始化数据库

```bash
python scripts/init_db.py
```

## 3) 两套运行流程

### A. 开发流程（`scripts/run_dev.sh`）

```bash
bash scripts/run_dev.sh
```

或直接：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### B. 生产流程（systemd）

1. 创建虚拟环境并安装依赖（参考上文）。
2. 准备环境变量（`.env`）。
3. 部署 `life-tracer.service` 到 `/etc/systemd/system/`。

`life-tracer.service` 示例：

```ini
[Unit]
Description=Life Tracer FastAPI Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/suibi
EnvironmentFile=/opt/suibi/.env
ExecStart=/opt/suibi/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启用与启动：

```bash
sudo cp life-tracer.service /etc/systemd/system/life-tracer.service
sudo systemctl daemon-reload
sudo systemctl enable --now life-tracer.service
sudo systemctl status life-tracer.service
```

## 4) Cloudflare Quick Tunnel（上线最短路径）

如果你只想最快速将本地/内网服务对外访问，可直接：

```bash
cloudflared tunnel --url http://127.0.0.1:8000
```

会输出 `https://*.trycloudflare.com` 的临时公网地址。

## 5) 备份与恢复

### 备份

已提供脚本：`scripts/backup.sh`，会打包以下内容：

- `app/`
- `scripts/`
- `requirements.txt`
- `.env`
- `data/`

执行：

```bash
bash scripts/backup.sh
```

可选指定输出目录：

```bash
bash scripts/backup.sh /path/to/backup_dir
```

### 恢复

详见：[`scripts/restore.md`](scripts/restore.md)

## 6) 迁移验证清单

迁移到新机器或新环境后，至少验证：

- [ ] 服务启动成功（`systemctl status life-tracer.service` 为 active/running）。
- [ ] 历史 entries 可见（打开首页并抽查旧数据）。
- [ ] imports 可读写（导入页可读取文件并成功入库）。
- [ ] exports 可读写（导出文件可生成并可下载/读取）。

## 7) 迁移总览

当前为 MVP 阶段，使用 `app/models.py` 中的 SQL 直接建表。
后续建议引入 Alembic 做版本化迁移：

1. 定义 SQLAlchemy 模型。
2. 初始化 Alembic 并生成首个 revision。
3. 使用 `alembic upgrade head` 执行迁移。

## 8) 认证与安全边界（MVP）

- 当前采用**单用户密码**登录，适合个人或小范围自托管场景。
- 登录失败按 `IP + 会话标识` 计数，连续失败 5 次锁定 10 分钟。
- 失败记录持久化在 SQLite 的 `auth_attempts` 表中，服务重启后不会丢失。
- 本方案仅用于 MVP 基础防护，**不替代企业级 IAM/SSO、多因素认证、细粒度 RBAC、审计合规能力**。
