# 便利店进销存系统

基于 Flask + MySQL + 原生 HTML 的简易便利店进销存系统

## 功能特性

- 用户登录（店长/店员权限控制）
- 商品进货/出货管理
- 库存查询和统计
- 日清月结报表
- 资金流水记录

## 安装和运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置数据库

1. 确保 MySQL 服务已启动
2. 执行提供的 SQL 脚本创建数据库和表
3. 修改 `app.py` 中的数据库配置信息

### 3. 运行项目

```bash
python app.py
```

访问 http://localhost:5000

## 测试账号

- 店长：用户名 `manager`，密码 `manager`
- 店员：用户名 `staff`，密码 `123456`

## 系统架构

- 后端：Flask (Python)
- 前端：原生 HTML + CSS + JavaScript
- 数据库：MySQL 5.7+
- 身份验证：Session + MD5 密码加密

## 文件结构

```
bs_shop/
├── app.py              # Flask主程序
├── requirements.txt    # Python依赖
├── README.md          # 说明文档
└── templates/         # HTML模板
    ├── login.html     # 登录页面
    ├── index.html     # 首页
    ├── transaction.html # 进货出货页面
    ├── stock.html     # 库存查询页面
    └── report.html    # 日清月结页面
```

## 使用说明

### 店长功能

- 商品进货/出货
- 库存查询
- 日清月结报表查看

### 店员功能

- 商品销售（出货）
- 库存查询

## 注意事项

1. 请确保 MySQL 数据库正常运行
2. 首次运行前请执行 SQL 脚本初始化数据
3. 修改 app.py 中的数据库连接配置
4. 生产环境请修改 Flask 的 secret_key
