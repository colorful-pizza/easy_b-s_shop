from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import pymysql
import hashlib
from datetime import datetime, timedelta
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # 修改为你的密钥

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',  # 修改为你的数据库用户名
    'password': 'root',  # 修改为你的数据库密码
    'database': 'shop',
    'charset': 'utf8mb4'
}

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)

def md5_encrypt(text):
    """MD5加密"""
    return hashlib.md5(text.encode()).hexdigest()

@app.route('/')
def index():
    """首页，检查登录状态"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', user=session)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'GET':
        return render_template('login.html')
    
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'message': '用户名和密码不能为空'})
    
    # MD5加密密码
    encrypted_password = md5_encrypt(password)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, username, role FROM users WHERE username = %s AND password = %s", 
                      (username, encrypted_password))
        user = cursor.fetchone()
        
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[2]
            return jsonify({'success': True, 'message': '登录成功'})
        else:
            return jsonify({'success': False, 'message': '用户名或密码错误'})
    finally:
        cursor.close()
        conn.close()

@app.route('/logout')
def logout():
    """退出登录"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/products')
def get_products():
    """获取所有商品"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, name, selling_price, cost_price, stock, image_url FROM products ORDER BY id")
        products = cursor.fetchall()
        
        result = []
        for product in products:
            result.append({
                'id': product[0],
                'name': product[1],
                'selling_price': float(product[2]),
                'cost_price': float(product[3]),
                'stock': product[4],
                'image_url': product[5]
            })
        
        return jsonify({'success': True, 'products': result})
    finally:
        cursor.close()
        conn.close()

@app.route('/purchase_action', methods=['POST'])
def purchase_action():
    """进货操作"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    if session['role'] != 'manager':
        return jsonify({'success': False, 'message': '权限不足，只有店长可以进货'})
    
    data = request.get_json()
    items = data.get('items', [])
    
    if not items:
        return jsonify({'success': False, 'message': '没有进货数据'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 生成采购单号
        now = datetime.now()
        order_no = f"PO{now.strftime('%Y%m%d%H%M%S')}"
        
        total_amount = 0
        
        # 检查商品并计算总金额
        for item in items:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 1)
            
            if not product_id or quantity <= 0:
                continue
            
            # 获取商品进价
            cursor.execute("SELECT cost_price FROM products WHERE id = %s", (product_id,))
            product_info = cursor.fetchone()
            
            if not product_info:
                return jsonify({'success': False, 'message': f'商品ID {product_id} 不存在'})
            
            cost_price = float(product_info[0])
            amount = cost_price * quantity
            total_amount += amount
        
        # 创建采购订单
        cursor.execute(
            "INSERT INTO purchase_orders (order_no, total_amount, order_time, user_id) VALUES (%s, %s, %s, %s)",
            (order_no, total_amount, now, session['user_id'])
        )
        
        # 创建采购明细并更新库存
        for item in items:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 1)
            
            if not product_id or quantity <= 0:
                continue
            
            # 获取商品进价
            cursor.execute("SELECT cost_price FROM products WHERE id = %s", (product_id,))
            cost_price = float(cursor.fetchone()[0])
            amount = cost_price * quantity
            
            # 插入采购明细
            cursor.execute(
                "INSERT INTO purchase_details (order_no, product_id, quantity, amount) VALUES (%s, %s, %s, %s)",
                (order_no, product_id, quantity, amount)
            )
            
            # 更新库存
            cursor.execute("UPDATE products SET stock = stock + %s WHERE id = %s", (quantity, product_id))
        
        conn.commit()
        return jsonify({'success': True, 'message': f'进货成功，订单号：{order_no}'})
    
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'进货失败: {str(e)}'})
    finally:
        cursor.close()
        conn.close()

@app.route('/sales_action', methods=['POST'])
def sales_action():
    """销售操作"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    data = request.get_json()
    items = data.get('items', [])
    
    if not items:
        return jsonify({'success': False, 'message': '没有销售数据'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 生成销售单号
        now = datetime.now()
        order_no = f"SO{now.strftime('%Y%m%d%H%M%S')}"
        
        total_amount = 0
        
        # 检查库存并计算总金额
        for item in items:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 1)
            
            if not product_id or quantity <= 0:
                continue
            
            # 获取商品售价和库存
            cursor.execute("SELECT selling_price, stock FROM products WHERE id = %s", (product_id,))
            product_info = cursor.fetchone()
            
            if not product_info:
                return jsonify({'success': False, 'message': f'商品ID {product_id} 不存在'})
            
            selling_price = float(product_info[0])
            current_stock = product_info[1]
            
            # 检查库存是否足够
            if current_stock < quantity:
                return jsonify({'success': False, 'message': f'商品ID {product_id} 库存不足'})
            
            amount = selling_price * quantity
            total_amount += amount
        
        # 创建销售订单
        cursor.execute(
            "INSERT INTO sales_orders (order_no, total_amount, order_time, user_id) VALUES (%s, %s, %s, %s)",
            (order_no, total_amount, now, session['user_id'])
        )
        
        # 创建销售明细并更新库存
        for item in items:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 1)
            
            if not product_id or quantity <= 0:
                continue
            
            # 获取商品售价
            cursor.execute("SELECT selling_price FROM products WHERE id = %s", (product_id,))
            selling_price = float(cursor.fetchone()[0])
            amount = selling_price * quantity
            
            # 插入销售明细
            cursor.execute(
                "INSERT INTO sales_details (order_no, product_id, quantity, amount) VALUES (%s, %s, %s, %s)",
                (order_no, product_id, quantity, amount)
            )
            
            # 更新库存
            cursor.execute("UPDATE products SET stock = stock - %s WHERE id = %s", (quantity, product_id))
        
        conn.commit()
        return jsonify({'success': True, 'message': f'销售成功，订单号：{order_no}'})
    
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'销售失败: {str(e)}'})
    finally:
        cursor.close()
        conn.close()

@app.route('/stock')
def stock():
    """库存查询页面"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('stock.html', user=session)

@app.route('/update_price', methods=['POST'])
def update_price():
    """更新商品价格（仅店长可用）"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    if session['role'] != 'manager':
        return jsonify({'success': False, 'message': '权限不足，只有店长可以修改价格'})
    
    data = request.get_json()
    product_id = data.get('product_id')
    selling_price = data.get('selling_price')
    cost_price = data.get('cost_price')
    
    if not product_id or selling_price is None or cost_price is None:
        return jsonify({'success': False, 'message': '参数不完整'})
    
    if selling_price <= 0 or cost_price <= 0:
        return jsonify({'success': False, 'message': '价格必须大于0'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "UPDATE products SET selling_price = %s, cost_price = %s WHERE id = %s",
            (selling_price, cost_price, product_id)
        )
        
        if cursor.rowcount > 0:
            conn.commit()
            return jsonify({'success': True, 'message': '价格更新成功'})
        else:
            return jsonify({'success': False, 'message': '商品不存在'})
    
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'})
    finally:
        cursor.close()
        conn.close()

@app.route('/purchase')
def purchase():
    """进货页面（仅店长可访问）"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session['role'] != 'manager':
        return redirect(url_for('index'))
    
    return render_template('purchase.html', user=session)

@app.route('/sales')
def sales():
    """销售页面"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('sales.html', user=session)

@app.route('/report')
def report():
    """日清月结页面"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 店员无权访问
    if session['role'] == 'staff':
        return redirect(url_for('index'))
    
    return render_template('report.html')

@app.route('/get_report', methods=['POST'])
def get_report():
    """获取报表数据"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    if session['role'] != 'manager':
        return jsonify({'success': False, 'message': '权限不足'})
    
    data = request.get_json()
    start_date = data.get('start_date', datetime.now().strftime('%Y-%m-%d'))
    end_date = data.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 获取指定时间段的销售收入
        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0) FROM sales_orders 
            WHERE DATE(order_time) BETWEEN %s AND %s
        """, (start_date, end_date))
        total_income = float(cursor.fetchone()[0])
        
        # 获取指定时间段的采购支出
        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0) FROM purchase_orders 
            WHERE DATE(order_time) BETWEEN %s AND %s
        """, (start_date, end_date))
        total_expense = float(cursor.fetchone()[0])
        
        profit = total_income - total_expense
        
        # 获取采购数量统计
        cursor.execute("""
            SELECT COALESCE(SUM(pd.quantity), 0) FROM purchase_details pd
            JOIN purchase_orders po ON pd.order_no = po.order_no
            WHERE DATE(po.order_time) BETWEEN %s AND %s
        """, (start_date, end_date))
        total_purchase = cursor.fetchone()[0]
        
        # 获取销售数量统计
        cursor.execute("""
            SELECT COALESCE(SUM(sd.quantity), 0) FROM sales_details sd
            JOIN sales_orders so ON sd.order_no = so.order_no
            WHERE DATE(so.order_time) BETWEEN %s AND %s
        """, (start_date, end_date))
        total_sales = cursor.fetchone()[0]
        
        # 获取历史总利润
        cursor.execute("""
            SELECT 
                COALESCE(SUM(so.total_amount), 0) - COALESCE(SUM(po.total_amount), 0) as total_profit
            FROM 
                (SELECT total_amount FROM sales_orders) so,
                (SELECT total_amount FROM purchase_orders) po
        """)
        total_profit_result = cursor.fetchone()
        total_profit = float(total_profit_result[0]) if total_profit_result[0] else 0
        
        # 重新计算历史总利润（更准确的方法）
        cursor.execute("SELECT COALESCE(SUM(total_amount), 0) FROM sales_orders")
        all_sales = float(cursor.fetchone()[0])
        cursor.execute("SELECT COALESCE(SUM(total_amount), 0) FROM purchase_orders")
        all_purchases = float(cursor.fetchone()[0])
        total_profit = all_sales - all_purchases
        
        # 获取详细流水（最近的销售和采购记录）
        cursor.execute("""
            (SELECT 
                so.order_time, so.order_no, '销售' as type, 
                so.total_amount, u.username,
                GROUP_CONCAT(CONCAT(p.name, '×', sd.quantity) SEPARATOR ', ') as products
            FROM sales_orders so
            JOIN sales_details sd ON so.order_no = sd.order_no
            JOIN products p ON sd.product_id = p.id
            JOIN users u ON so.user_id = u.id
            WHERE DATE(so.order_time) BETWEEN %s AND %s
            GROUP BY so.order_no)
            UNION ALL
            (SELECT 
                po.order_time, po.order_no, '采购' as type,
                po.total_amount, u.username,
                GROUP_CONCAT(CONCAT(p.name, '×', pd.quantity) SEPARATOR ', ') as products
            FROM purchase_orders po
            JOIN purchase_details pd ON po.order_no = pd.order_no
            JOIN products p ON pd.product_id = p.id
            JOIN users u ON po.user_id = u.id
            WHERE DATE(po.order_time) BETWEEN %s AND %s
            GROUP BY po.order_no)
            ORDER BY order_time DESC
            LIMIT 20
        """, (start_date, end_date, start_date, end_date))
        details = cursor.fetchall()
        
        detail_list = []
        for detail in details:
            detail_list.append({
                'time': detail[0].strftime('%Y-%m-%d %H:%M:%S'),
                'order_no': detail[1],
                'type': detail[2],
                'amount': float(detail[3]),
                'username': detail[4],
                'products': detail[5]
            })
        
        return jsonify({
            'success': True,
            'data': {
                'total_income': total_income,
                'total_expense': total_expense,
                'profit': profit,
                'total_purchase': total_purchase,
                'total_sales': total_sales,
                'total_profit': total_profit,
                'details': detail_list
            }
        })
    
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
