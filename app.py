"""
便利店进销存系统 - Flask主应用
"""
from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from werkzeug.exceptions import HTTPException
import os
import traceback

# 导入API蓝图
from api.auth import auth_bp
from api.products import products_bp
from api.suppliers import suppliers_bp
from api.customers import customers_bp
from api.purchase import purchase_bp
from api.sales import sales_bp
from api.inventory import inventory_bp
from api.reports import reports_bp
from printing import printing_bp

def create_app(config=None):
    """创建Flask应用"""
    app = Flask(__name__)
    
    # 应用配置
    app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
    app.config['JSON_AS_ASCII'] = False  # 支持中文JSON
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True  # 美化JSON输出
    
    # 数据库配置
    app.config['DATABASE'] = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': '123456',
        'database': 'shop',
        'charset': 'utf8mb4'
    }
    
    # 注册蓝图
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(suppliers_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(purchase_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(printing_bp)
    
    # 全局错误处理
    @app.errorhandler(Exception)
    def handle_exception(e):
        """处理所有异常"""
        if isinstance(e, HTTPException):
            return jsonify({
                'success': False,
                'message': e.description
            }), e.code
        
        # 记录详细错误信息
        app.logger.error(f'Internal Server Error: {str(e)}')
        app.logger.error(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'message': '服务器内部错误'
        }), 500
    
    @app.errorhandler(404)
    def not_found(e):
        """处理404错误"""
        return jsonify({
            'success': False,
            'message': '请求的资源不存在'
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(e):
        """处理405错误"""
        return jsonify({
            'success': False,
            'message': '不支持的HTTP方法'
        }), 405
    
    # 请求前处理
    @app.before_request
    def before_request():
        """请求前处理"""
        # 打印请求信息（开发模式）
        if app.debug:
            print(f'{request.method} {request.path} - {request.remote_addr}')
    
    # 请求后处理
    @app.after_request
    def after_request(response):
        """请求后处理 - 添加CORS头"""
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    # 健康检查端点
    @app.route('/health')
    def health_check():
        """健康检查"""
        return jsonify({
            'success': True,
            'message': '服务正常运行',
            'version': '1.0.0'
        })
    
    # 页面路由
    @app.route('/')
    def index():
        """主页"""
        return render_template('index.html')
    
    @app.route('/login')
    def login_page():
        """登录页面"""
        return render_template('login.html')
    
    @app.route('/sales')
    def sales_page():
        """商品销售页面"""
        return render_template('sales.html')
    
    @app.route('/inventory')
    def inventory_page():
        """库存查询页面"""
        return render_template('inventory.html')
    
    @app.route('/products')
    def products_page():
        """商品管理页面"""
        return render_template('products.html')
    
    @app.route('/purchase')
    def purchase_page():
        """采购管理页面"""
        return render_template('purchase.html')
    
    @app.route('/incoming')
    def incoming_page():
        """进货管理页面"""
        return render_template('incoming.html')
    
    @app.route('/customers')
    def customers_page():
        """客户管理页面"""
        return render_template('customers.html')
    
    @app.route('/suppliers')
    def suppliers_page():
        """供应商管理页面"""
        return render_template('suppliers.html')
    
    @app.route('/payables')
    def payables_page():
        """应付结算页面"""
        return render_template('payables.html')

    @app.route('/stockcheck')
    def stockcheck_page():
        """库存盘点页面"""
        return render_template('stockcheck.html')
    
    @app.route('/reports')
    def reports_page():
        """报表分析页面"""
        return render_template('reports.html')
    
    @app.route('/debug')
    def debug_page():
        """调试页面"""
        return render_template('debug.html')
    
    # API信息端点
    @app.route('/api/info')
    def api_info():
        """API信息"""
        return jsonify({
            'success': True,
            'data': {
                'name': '便利店进销存系统',
                'version': '1.0.0',
                'description': '基于Flask + MySQL的便利店进销存管理系统',
                'endpoints': {
                    'auth': [
                        'POST /api/auth/login',
                        'POST /api/auth/logout',
                        'GET /api/auth/users',
                        'POST /api/auth/users',
                        'PUT /api/auth/users/{id}',
                        'DELETE /api/auth/users/{id}',
                        'PUT /api/auth/change-password'
                    ],
                    'products': [
                        'GET /api/products',
                        'POST /api/products',
                        'PUT /api/products/{id}',
                        'DELETE /api/products/{id}',
                        'GET /api/products/search'
                    ],
                    'suppliers': [
                        'GET /api/suppliers',
                        'POST /api/suppliers',
                        'PUT /api/suppliers/{id}',
                        'DELETE /api/suppliers/{id}',
                        'GET /api/suppliers/search'
                    ],
                    'customers': [
                        'GET /api/customers',
                        'POST /api/customers',
                        'PUT /api/customers/{id}',
                        'DELETE /api/customers/{id}',
                        'GET /api/customers/default'
                    ],
                    'purchase': [
                        'GET /api/purchase/orders',
                        'POST /api/purchase/orders',
                        'PUT /api/purchase/orders/{id}/approve',
                        'PUT /api/purchase/orders/{id}/reject',
                        'GET /api/purchase/incoming',
                        'POST /api/purchase/incoming',
                        'PUT /api/purchase/incoming/{id}/complete'
                    ],
                    'sales': [
                        'GET /api/sales/outgoing',
                        'POST /api/sales/outgoing',
                        'GET /api/sales/summary'
                    ],
                    'inventory': [
                        'GET /api/inventory',
                        'GET /api/inventory/alerts',
                        'GET /api/inventory/stats',
                        'GET /api/inventory/checks',
                        'POST /api/inventory/checks',
                        'PUT /api/inventory/checks/{id}/complete'
                    ],
                    'reports': [
                        'GET /api/reports/dashboard',
                        'GET /api/reports/sales',
                        'GET /api/reports/purchase',
                        'GET /api/reports/inventory',
                        'GET /api/reports/profit'
                    ]
                }
            }
        })
    
    return app

def init_app():
    """初始化应用"""
    app = create_app()
    
    # 设置日志
    if not app.debug:
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            'logs/bs_shop.log', 
            maxBytes=10240000, 
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('便利店进销存系统启动')
    
    return app

if __name__ == '__main__':
    app = init_app()
    
    print("=" * 50)
    print("便利店进销存系统")
    print("=" * 50)
    print("系统启动中...")
    print(f"访问地址: http://localhost:5000")
    print(f"API信息: http://localhost:5000/api/info")
    print(f"健康检查: http://localhost:5000/health")
    print("=" * 50)
    
    # 启动开发服务器
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )