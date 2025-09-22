# 便利店进销存系统（Flask + MySQL）

一个覆盖“采购-入库-销售-库存-盘点-应付结算-报表-打印”的轻量级进销存系统，支持店员/店长角色与票据打印。

演示数据：`init_database.sql` 已内置完整样例（用户、客户、供应商、商品、采购单各状态、入库记录、销售流水、盘点单、应付未结算），导入后即可开箱体验全流程与报表。

## 功能特性

- 用户与权限：店长（manager）/店员（staff），登录、密码修改
- 商品管理：增删改查、条码/编码、分类、品牌、单位、售价
- 库存管理：库存查询、低库存预警、统计
- 采购流程：申请（pending）→ 审批（approved）→ 交付（delivered）→ 入库（stock）→ 付款（paid）/取消（cancelled）
- 入库管理：关联采购单入库或独立入库（含批次、生产/到期日）
- 销售 POS：扫码/输入编码加购、购物车、结账（默认客户“散户”）、自动计算利润
- 应付结算：按供应商汇总未结算采购单，支持结算与打印供应商对账单
- 盘点管理：创建盘点、录入实际数、自动生成盘盈/盘亏并可“完成盘点”调整库存
- 报表分析：今日/昨日/本月 KPI、近 7 天趋势、Top10 商品、库存概览与分类统计
- 打印中心：
  - 销售小票：结账后可勾选自动打印
  - 采购单：待定打印“采购申请单”，已批准打印“采购订单”
  - 应付结算：供应商对账单打印
  - 盘点：盘点作业单（“实际数”留空线下填写）

## 技术栈

- 后端：Flask、Blueprints、原生 MySQL 访问
- 前端：Jinja2 + 原生 JS + 少量 CSS（`static/css/style.css`）
- 数据库：MySQL 8（推荐）/5.7 兼容，字符集 utf8mb4

## 目录结构

```
app.py
init_database.sql
requirements.txt
templates/
	index.html login.html sales.html purchase.html stock.html stock_new.html
	transaction.html report.html reports.html suppliers.html payables.html stockcheck.html
	printing/
		receipt.html purchase_apply.html purchase_order.html supplier_statement.html stockcheck_sheet.html
static/
	css/style.css
	js/common.js
api/  # auth, products, suppliers, customers, purchase, sales, inventory, reports
printing/  # receipt, purchase, payables, stockcheck 蓝图及路由
```

## 快速开始（Windows PowerShell）

1. 安装依赖

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
```

2. 准备 MySQL 与数据库

- 创建数据库：

```sql
CREATE DATABASE IF NOT EXISTS `shop` DEFAULT CHARACTER SET utf8mb4;
```

- 在 MySQL 客户端执行初始化脚本：将 `init_database.sql` 导入到 `shop` 数据库。

3. 配置数据库连接（如有需要）

- `app.py` 中默认使用：host=localhost, port=3306, user=root, password=123456, database=shop
- 如有差异，请修改 `create_app` 中的 `app.config['DATABASE']`

4. 启动应用

```powershell
python app.py
```

访问：http://localhost:5000 ；健康检查：http://localhost:5000/health

## 默认账号

- 管理员：用户名 `admin`，密码 `123456`
- 店员：用户名 `staff01`，密码 `123456`

上述用户已在 `init_database.sql` 中写入（密码为 MD5 32 位小写，后端按项目逻辑校验）。

## 打印与报表

- 打印入口统一在“打印中心”蓝图下：
  - 销售小票：/printing/receipt/<order_id>
  - 采购申请：/printing/purchase/apply/<id>
  - 采购订单：/printing/purchase/order/<id>
  - 供应商对账单：/printing/payables/statement/<supplier_id>
  - 盘点作业单：/printing/stockcheck/sheet/<check_id>
- 页面侧栏已提供按钮：

  - 销售结账后可勾选“下单后打印小票”
  - 采购列表根据状态展示对应打印按钮
  - 应付结算页“打印对账单”
  - 盘点详情页“打印盘点单”（进行中可用）

- 报表页 `/reports` 展示：
  - 今日/昨日/本月 KPI（销售额、订单数、利润等）
  - 近 7 天销售趋势（内置 SVG 折线图）
  - Top10 商品（销量前十）
  - 库存概览与分类统计

## 初始化数据说明（重点）

`init_database.sql` 已覆盖：

- 采购单各状态：pending、approved、delivered、stock、paid、cancelled
- 入库记录：含批次、生产/到期日
- 销售流水：近 7 天多笔交易，含利润字段
- 盘点：1 个已完成（会调整库存）、1 个进行中
- 应付未结算：包含 delivered/stock 状态的采购单用于对账
- 末尾自动“同步库存”脚本：以“入库合计 - 销售合计 + 已完成盘点差异”计算，确保导入后库存与业务一致

导入后即可直接在页面体验：库存预警、采购打印、应付对账打印、盘点打印、报表趋势图与 Top10 等。

## 许可

仅用于学习与教学示例，生产环境请根据自身需求完善安全、审计、备份、权限控制等能力。
