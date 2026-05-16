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

## 3) 开发启动

```bash
bash scripts/run_dev.sh
```

或直接：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 4) 部署总览

- 生产环境建议使用 `gunicorn + uvicorn workers` 或系统服务托管。
- 将 `.env` 中敏感配置通过安全方式注入（如 CI/CD secret、容器环境变量）。
- 部署前先运行 `python scripts/init_db.py` 完成数据库初始化。

## 5) 迁移总览

当前为 MVP 阶段，使用 `app/models.py` 中的 SQL 直接建表。
后续建议引入 Alembic 做版本化迁移：

1. 定义 SQLAlchemy 模型。
2. 初始化 Alembic 并生成首个 revision。
3. 使用 `alembic upgrade head` 执行迁移。

## 6) 认证与安全边界（MVP）

- 当前采用**单用户密码**登录，适合个人或小范围自托管场景。
- 登录失败按 `IP + 会话标识` 计数，连续失败 5 次锁定 10 分钟。
- 失败记录持久化在 SQLite 的 `auth_attempts` 表中，服务重启后不会丢失。
- 本方案仅用于 MVP 基础防护，**不替代企业级 IAM/SSO、多因素认证、细粒度 RBAC、审计合规能力**。
