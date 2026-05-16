# 恢复流程（新机器）

## 1) 解包备份

将备份包上传到新机器并解压到目标目录：

```bash
mkdir -p /opt/suibi
cd /opt/suibi
tar -xzf /path/to/suibi_release_YYYYmmdd_HHMMSS.tar.gz
```

## 2) 创建 venv 并安装依赖

```bash
cd /opt/suibi
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3) 数据库初始化（按需）

> 如果恢复包中已有完整 `data/` 且数据文件可用，通常不需要再次初始化。

```bash
source .venv/bin/activate
python scripts/init_db.py
```

## 4) 启动 systemd 服务

```bash
sudo cp deploy/life-tracer.service /etc/systemd/system/life-tracer.service
sudo systemctl daemon-reload
sudo systemctl enable --now life-tracer.service
sudo systemctl status life-tracer.service
```
