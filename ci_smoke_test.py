"""
最小冒烟测试：
- 导入 Flask 应用（init_app 或 create_app）
- 使用 test_client 请求 /health 返回 200 且 success=True
不依赖数据库连接。
"""
import importlib

app = None

try:
    mod = importlib.import_module("app")
    if hasattr(mod, "init_app"):
        app = mod.init_app()
    elif hasattr(mod, "create_app"):
        app = mod.create_app()
except Exception as e:
    raise SystemExit(f"导入应用失败: {e}")

if app is None:
    raise SystemExit("未能创建 Flask app 实例")

client = app.test_client()
resp = client.get("/health")
assert resp.status_code == 200, f"/health 状态码: {resp.status_code}"
try:
    data = resp.get_json()
except Exception:
    data = None
assert isinstance(data, dict) and data.get("success") is True, f"/health 响应体: {data}"
print("OK: /health passed")
