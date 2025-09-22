# 便利店进销存系统

最简 CI 与在线展示说明。

## 持续集成（CI）

- 已添加 GitHub Actions 工作流：`.github/workflows/ci.yml`
- 内容：安装最小依赖，语法检查，运行 `ci_smoke_test.py` 访问 `/health`
- 使用方法：推送到 GitHub 仓库的任意分支，Actions 将自动触发。

## 本地运行（开发）

- 需要 Python 3.10+/3.11
- 安装依赖：`pip install -r requirements.txt`
- 启动：`python app.py`，访问 http://localhost:5000

## 在线展示（最简）

- 方案 A：使用 ngrok/Cloudflare Tunnel 暴露本地 5000 端口
- 方案 B：在云服务器上 `pip install -r requirements.txt` 并 `python app.py`，放行 5000 端口对外访问。

> 提示：业务接口大多依赖 MySQL，如仅演示页面和健康检查，CI 已不依赖数据库；真实功能需先导入 `init_database.sql` 并可用 `create_test_users.py` 创建测试账号。
