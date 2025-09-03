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
        cursor.execute("SELECT id, name, price, stock, image_url FROM products ORDER BY id")
        products = cursor.fetchall()
        
        result = []
        for product in products:
            result.append({
                'id': product[0],
                'name': product[1],
                'price': float(product[2]),
                'stock': product[3],
                'image_url': product[4]
            })
        
        return jsonify({'success': True, 'products': result})
    finally:
        cursor.close()
        conn.close()

@app.route('/inventory_action', methods=['POST'])
def inventory_action():
    """进货/出货操作"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    data = request.get_json()
    actions = data.get('actions', [])
    
    if not actions:
        return jsonify({'success': False, 'message': '没有操作数据'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        for action in actions:
            product_id = action.get('product_id')
            action_type = action.get('action')  # 'in' 或 'out'
            quantity = action.get('quantity', 1)
            
            if not product_id or not action_type or quantity <= 0:
                continue
            
            # 获取商品价格
            cursor.execute("SELECT price, stock FROM products WHERE id = %s", (product_id,))
            product_info = cursor.fetchone()
            
            if not product_info:
                continue
            
            price = float(product_info[0])
            current_stock = product_info[1]
            
            # 检查出货时库存是否足够
            if action_type == 'out' and current_stock < quantity:
                return jsonify({'success': False, 'message': f'商品ID {product_id} 库存不足'})
            
            # 更新库存
            if action_type == 'in':
                cursor.execute("UPDATE products SET stock = stock + %s WHERE id = %s", (quantity, product_id))
                amount = price * quantity  # 进货成本
                finance_type = 'out'  # 资金流出
            else:  # 'out'
                cursor.execute("UPDATE products SET stock = stock - %s WHERE id = %s", (quantity, product_id))
                amount = price * quantity  # 销售收入
                finance_type = 'in'  # 资金流入
            
            # 记录库存流水
            cursor.execute(
                "INSERT INTO inventory_log (product_id, action, quantity, action_time, user_id) VALUES (%s, %s, %s, %s, %s)",
                (product_id, action_type, quantity, datetime.now(), session['user_id'])
            )
            
            # 记录资金流水
            cursor.execute(
                "INSERT INTO finance_log (type, amount, time, user_id) VALUES (%s, %s, %s, %s)",
                (finance_type, amount, datetime.now(), session['user_id'])
            )
        
        conn.commit()
        return jsonify({'success': True, 'message': '操作成功'})
    
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})
    finally:
        cursor.close()
        conn.close()

@app.route('/stock')
def stock():
    """库存查询页面"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('stock.html')

@app.route('/transaction')
def transaction():
    """进货出货页面"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 检查权限：店员只能访问出货功能
    if session['role'] == 'staff':
        return render_template('transaction.html', user=session)
    
    return render_template('transaction.html', user=session)

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
    
    if session['role'] == 'staff':
        return jsonify({'success': False, 'message': '权限不足'})
    
    data = request.get_json()
    start_date = data.get('start_date', datetime.now().strftime('%Y-%m-%d'))
    end_date = data.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 获取指定时间段的资金流水
        cursor.execute("""
            SELECT type, SUM(amount) FROM finance_log 
            WHERE DATE(time) BETWEEN %s AND %s 
            GROUP BY type
        """, (start_date, end_date))
        finance_data = cursor.fetchall()
        
        total_income = 0
        total_expense = 0
        for item in finance_data:
            if item[0] == 'in':
                total_income = float(item[1])
            else:
                total_expense = float(item[1])
        
        profit = total_income - total_expense
        
        # 获取库存流水统计
        cursor.execute("""
            SELECT action, SUM(quantity) FROM inventory_log 
            WHERE DATE(action_time) BETWEEN %s AND %s 
            GROUP BY action
        """, (start_date, end_date))
        inventory_data = cursor.fetchall()
        
        total_in = 0
        total_out = 0
        for item in inventory_data:
            if item[0] == 'in':
                total_in = item[1]
            else:
                total_out = item[1]
        
        # 获取历史总利润
        cursor.execute("SELECT SUM(CASE WHEN type='in' THEN amount ELSE -amount END) FROM finance_log")
        total_profit_result = cursor.fetchone()
        total_profit = float(total_profit_result[0]) if total_profit_result[0] else 0
        
        # 获取详细流水
        cursor.execute("""
            SELECT il.action_time, p.name, il.action, il.quantity, 
                   fl.type, fl.amount, u.username
            FROM inventory_log il
            JOIN products p ON il.product_id = p.id
            JOIN finance_log fl ON DATE(il.action_time) = DATE(fl.time) AND il.user_id = fl.user_id
            JOIN users u ON il.user_id = u.id
            WHERE DATE(il.action_time) BETWEEN %s AND %s
            ORDER BY il.action_time DESC
            LIMIT 50
        """, (start_date, end_date))
        details = cursor.fetchall()
        
        detail_list = []
        for detail in details:
            detail_list.append({
                'time': detail[0].strftime('%Y-%m-%d %H:%M:%S'),
                'product_name': detail[1],
                'action': '进货' if detail[2] == 'in' else '出货',
                'quantity': detail[3],
                'finance_type': '收入' if detail[4] == 'in' else '支出',
                'amount': float(detail[5]),
                'username': detail[6]
            })
        
        return jsonify({
            'success': True,
            'data': {
                'total_income': total_income,
                'total_expense': total_expense,
                'profit': profit,
                'total_in': total_in,
                'total_out': total_out,
                'total_profit': total_profit,
                'details': detail_list
            }
        })
    
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
