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
3. 使用仓库内示例：`deploy/life-tracer.service`（按实际机器修改 User/Group/WorkingDirectory）。

启用与启动：

```bash
sudo cp deploy/life-tracer.service /etc/systemd/system/life-tracer.service
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

已提供脚本：`scripts/backup.sh`（全量备份）与 `scripts/package_release.sh`（迁移发布包）。

`package_release.sh` 默认打包以下内容（可选包含 `.env`）：

- `app/`
- `scripts/`
- `requirements.txt`
- `.env.example`
- `README.md`
- `data/`（存在时）

执行：

```bash
bash scripts/backup.sh
```

可选指定输出目录：

```bash
bash scripts/backup.sh /path/to/backup_dir

# 迁移发布包（推荐）
bash scripts/package_release.sh releases true
```

### 恢复

优先使用自动恢复脚本：

```bash
bash scripts/restore.sh /path/to/suibi_release_YYYYmmdd_HHMMSS.tar.gz /opt/suibi
```

手动恢复步骤详见：[`scripts/restore.md`](scripts/restore.md)


## 6) 30分钟迁移 SOP（最短路径）

### 打包端（旧机器）

```bash
cd /path/to/notes_suibi
bash scripts/package_release.sh releases true
# 产物示例：releases/suibi_release_YYYYmmdd_HHMMSS.tar.gz
```

> 参数 `true` 表示可选包含 `.env`；若不想打包 `.env`，可省略该参数。

### 恢复端（新机器）

```bash
mkdir -p /opt/suibi
cd /opt/suibi
# 假设备份包已上传到 /tmp
bash scripts/restore.sh /tmp/suibi_release_YYYYmmdd_HHMMSS.tar.gz /opt/suibi

# 启用 systemd
sudo cp /opt/suibi/deploy/life-tracer.service /etc/systemd/system/life-tracer.service
sudo systemctl daemon-reload
sudo systemctl enable --now life-tracer.service

# 迁移后快速自检
cd /opt/suibi
bash scripts/smoke_check.sh http://127.0.0.1:8000
```

## 7) 迁移验证清单

迁移到新机器或新环境后，至少验证：

- [ ] 服务启动成功（`systemctl status life-tracer.service` 为 active/running）。
- [ ] 历史 entries 可见（打开首页并抽查旧数据）。
- [ ] imports 可读写（导入页可读取文件并成功入库）。
- [ ] exports 可读写（导出文件可生成并可下载/读取）。

## 8) 迁移总览

当前为 MVP 阶段，使用 `app/models.py` 中的 SQL 直接建表。
后续建议引入 Alembic 做版本化迁移：

1. 定义 SQLAlchemy 模型。
2. 初始化 Alembic 并生成首个 revision。
3. 使用 `alembic upgrade head` 执行迁移。

## 9) 认证与安全边界（MVP）

- 当前采用**单用户密码**登录，适合个人或小范围自托管场景。
- 登录失败按 `IP + 会话标识` 计数，连续失败 5 次锁定 10 分钟。
- 失败记录持久化在 SQLite 的 `auth_attempts` 表中，服务重启后不会丢失。
- 本方案仅用于 MVP 基础防护，**不替代企业级 IAM/SSO、多因素认证、细粒度 RBAC、审计合规能力**。


## 10) Schema 版本与变更日志

当前 schema 版本：`v1`（通过 SQLite `PRAGMA user_version` 管理）。

### 字段命名策略（统一约定）

- 状态类字段统一使用 `*_status` 后缀（如 `parse_status`、`llm_status`）。
- 避免布尔字段与枚举字段表达同一语义（例如 `manual` 与 `source_type=manual` 二选一，旧字段仅保留兼容）。
- 历史兼容字段不立即删除，后续通过 `migrations/` 增量迁移。

### 变更日志

- **v1 (2026-05-16)**
  - 建立 `migrations/` 目录，预留跨机器升级脚本入口。
  - 增加 `migrations/0001_baseline_schema_v1.sql`，记录命名规范与兼容策略。
  - 增加 `migrations/0002_session_turns_status_alignment.sql`，对齐 `session_turns.llm_status`。
  - `scripts/init_db.py` 增加幂等版本检查提示，避免误以为会覆盖已有数据。
  - `app/db.py` 在初始化阶段写入 schema 版本，并对 `session_turns.llm_status` 做幂等补齐。
