"""
销售管理API模块
"""
from flask import Blueprint, request, jsonify
from utils.database import get_db_connection, get_db_dict_connection
from utils.auth import login_required, get_current_user
from utils.helpers import validate_required_fields, generate_order_no, format_datetime, format_date, safe_float, safe_int
from datetime import datetime

sales_bp = Blueprint('sales', __name__)

@sales_bp.route('/api/outgoing-orders', methods=['GET'])
@login_required
def get_outgoing_orders():
    """获取销售订单列表（分页）"""
    try:
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 10))
        search = request.args.get('search', '').strip()
        customer_id = request.args.get('customer_id', '').strip()
        start_date = request.args.get('start_date', '').strip()
        end_date = request.args.get('end_date', '').strip()
        
        conn = get_db_dict_connection()
        cursor = conn.cursor()
        
        # 构建查询条件
        where_conditions = []
        params = []
        
        if search:
            where_conditions.append("(oo.order_no LIKE %s OR c.name LIKE %s OR u.real_name LIKE %s)")
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
        
        if customer_id:
            where_conditions.append("oo.customer_id = %s")
            params.append(customer_id)
        
        if start_date:
            where_conditions.append("oo.sale_date >= %s")
            params.append(start_date)
        
        if end_date:
            where_conditions.append("oo.sale_date <= %s")
            params.append(end_date)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # 计数查询
        count_query = f"""
            SELECT COUNT(*) 
            FROM outgoing_orders oo
            LEFT JOIN customers c ON oo.customer_id = c.id
            LEFT JOIN users u ON oo.user_id = u.id
            {where_clause}
        """
        cursor.execute(count_query, params)
        total = cursor.fetchone()['COUNT(*)']
        
        # 数据查询
        offset = (page - 1) * size
        data_query = f"""
            SELECT oo.id, oo.order_no, oo.customer_id, c.name as customer_name,
                   oo.total_amount, oo.total_cost, oo.profit,
                   oo.sale_date, oo.user_id, u.real_name as user_name,
                   oo.created_at, oo.remark
            FROM outgoing_orders oo
            LEFT JOIN customers c ON oo.customer_id = c.id
            LEFT JOIN users u ON oo.user_id = u.id
            {where_clause}
            ORDER BY oo.sale_date DESC, oo.created_at DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(data_query, params + [size, offset])
        orders = cursor.fetchall()
        
        # 格式化数据
        for order in orders:
            order['total_amount'] = float(order['total_amount']) if order['total_amount'] else 0
            order['total_cost'] = float(order['total_cost']) if order['total_cost'] else 0
            order['profit'] = float(order['profit']) if order['profit'] else 0
            order['sale_date'] = format_date(order['sale_date'])
            order['created_at'] = format_datetime(order['created_at'])
        
        cursor.close()
        conn.close()
        
        # 计算分页信息
        total_pages = (total + size - 1) // size
        
        return jsonify({
            'success': True,
            'data': orders,
            'pagination': {
                'page': page,
                'size': size,
                'total': total,
                'total_pages': total_pages,
                'has_prev': page > 1,
                'has_next': page < total_pages
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取销售订单列表失败: {str(e)}'
        }), 500

@sales_bp.route('/api/outgoing-orders/<int:order_id>', methods=['GET'])
@login_required
def get_outgoing_order(order_id):
    """获取销售订单详情"""
    try:
        conn = get_db_dict_connection()
        cursor = conn.cursor()
        
        # 获取订单基本信息
        cursor.execute("""
            SELECT oo.id, oo.order_no, oo.customer_id, c.name as customer_name,
                   oo.total_amount, oo.total_cost, oo.profit,
                   oo.sale_date, oo.user_id, u.real_name as user_name,
                   oo.created_at, oo.remark
            FROM outgoing_orders oo
            LEFT JOIN customers c ON oo.customer_id = c.id
            LEFT JOIN users u ON oo.user_id = u.id
            WHERE oo.id = %s
        """, (order_id,))
        
        order = cursor.fetchone()
        if not order:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '销售订单不存在'
            }), 404
        
        # 获取订单明细
        cursor.execute("""
            SELECT od.id, od.product_id, p.code, p.name as product_name, p.unit,
                   od.quantity, od.selling_price, od.cost_price, 
                   od.amount, od.cost_amount, od.profit, od.remark
            FROM outgoing_details od
            LEFT JOIN products p ON od.product_id = p.id
            WHERE od.outgoing_id = %s
            ORDER BY od.id
        """, (order_id,))
        
        details = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # 格式化数据
        order['total_amount'] = float(order['total_amount']) if order['total_amount'] else 0
        order['total_cost'] = float(order['total_cost']) if order['total_cost'] else 0
        order['profit'] = float(order['profit']) if order['profit'] else 0
        order['sale_date'] = format_date(order['sale_date'])
        order['created_at'] = format_datetime(order['created_at'])
        
        for detail in details:
            detail['selling_price'] = float(detail['selling_price'])
            detail['cost_price'] = float(detail['cost_price'])
            detail['amount'] = float(detail['amount'])
            detail['cost_amount'] = float(detail['cost_amount'])
            detail['profit'] = float(detail['profit'])
        
        return jsonify({
            'success': True,
            'data': {
                'order': order,
                'details': details
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取销售订单详情失败: {str(e)}'
        }), 500

@sales_bp.route('/api/outgoing-orders', methods=['POST'])
@login_required
def create_outgoing_order():
    """创建销售订单"""
    try:
        data = request.get_json() or {}
        
        # 验证必填字段
        required_fields = ['sale_date', 'details']
        is_valid, message = validate_required_fields(data, required_fields)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': message
            })
        
        customer_id = safe_int(data.get('customer_id', 0)) or None
        sale_date = data['sale_date']
        details = data['details']
        remark = data.get('remark', '').strip()
        
        if not details or len(details) == 0:
            return jsonify({
                'success': False,
                'message': '销售明细不能为空'
            })
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 如果指定了客户，验证客户是否存在
            if customer_id:
                cursor.execute("SELECT id FROM customers WHERE id = %s AND status = 'active'", (customer_id,))
                if not cursor.fetchone():
                    return jsonify({
                        'success': False,
                        'message': '客户不存在或已禁用'
                    })
            else:
                # 获取默认客户（散户）
                cursor.execute("SELECT id FROM customers WHERE is_default = 1 LIMIT 1")
                default_customer = cursor.fetchone()
                if default_customer:
                    customer_id = default_customer[0]
            
            # 验证商品并计算总金额和利润
            total_amount = 0
            total_cost = 0
            total_profit = 0
            validated_details = []
            
            for detail in details:
                product_id = safe_int(detail.get('product_id'))
                quantity = safe_int(detail.get('quantity'))
                selling_price = safe_float(detail.get('selling_price'))
                cost_price = safe_float(detail.get('cost_price', 0))
                detail_remark = detail.get('remark', '').strip()
                
                if not product_id or quantity <= 0 or selling_price <= 0:
                    return jsonify({
                        'success': False,
                        'message': '销售明细数据不完整或无效'
                    })
                
                # 验证商品是否存在和库存是否充足
                cursor.execute("""
                    SELECT p.id, p.selling_price, COALESCE(i.quantity, 0) as stock_quantity
                    FROM products p
                    LEFT JOIN inventory i ON p.id = i.product_id
                    WHERE p.id = %s AND p.status = 'active'
                """, (product_id,))
                product = cursor.fetchone()
                
                if not product:
                    return jsonify({
                        'success': False,
                        'message': f'商品ID {product_id} 不存在或已禁用'
                    })
                
                if product[2] < quantity:  # stock_quantity
                    return jsonify({
                        'success': False,
                        'message': f'商品ID {product_id} 库存不足，当前库存：{product[2]}'
                    })
                
                # 如果没有指定成本价，使用最近的进货成本价
                if cost_price <= 0:
                    cursor.execute("""
                        SELECT id.cost_price
                        FROM incoming_details id
                        INNER JOIN incoming_orders io ON id.incoming_id = io.id
                        WHERE id.product_id = %s
                        ORDER BY io.incoming_date DESC, io.created_at DESC
                        LIMIT 1
                    """, (product_id,))
                    last_cost = cursor.fetchone()
                    cost_price = safe_float(last_cost[0]) if last_cost else 0.0
                
                # 统一使用 float 参与计算，避免 float 与 Decimal 混算
                selling_price = safe_float(selling_price)
                cost_price = safe_float(cost_price)
                amount = float(quantity) * selling_price
                cost_amount = float(quantity) * cost_price
                profit = amount - cost_amount
                
                total_amount += amount
                total_cost += cost_amount
                total_profit += profit
                
                validated_details.append({
                    'product_id': product_id,
                    'quantity': quantity,
                    'selling_price': selling_price,
                    'cost_price': cost_price,
                    'amount': amount,
                    'cost_amount': cost_amount,
                    'profit': profit,
                    'remark': detail_remark
                })
            
            # 生成订单号
            order_no = generate_order_no('OUT')
            current_user = get_current_user()
            
            # 插入销售订单
            cursor.execute("""
                INSERT INTO outgoing_orders (order_no, customer_id, total_amount, 
                                           total_cost, profit, sale_date, user_id, remark)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (order_no, customer_id, float(total_amount), float(total_cost), float(total_profit),
                  sale_date, current_user['user_id'], remark or None))
            
            order_id = cursor.lastrowid
            
            # 插入销售明细并更新库存
            for detail in validated_details:
                cursor.execute("""
                    INSERT INTO outgoing_details (outgoing_id, product_id, quantity, 
                                                selling_price, cost_price, amount, 
                                                cost_amount, profit, remark)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (order_id, detail['product_id'], int(detail['quantity']),
                      float(detail['selling_price']), float(detail['cost_price']), float(detail['amount']),
                      float(detail['cost_amount']), float(detail['profit']), detail['remark'] or None))
                
                # 更新库存（减少）
                cursor.execute("""
                    UPDATE inventory 
                    SET quantity = quantity - %s, updated_at = NOW()
                    WHERE product_id = %s
                """, (detail['quantity'], detail['product_id']))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': '销售订单创建成功',
                'data': {
                    'order_id': order_id,
                    'order_no': order_no,
                    'total_amount': total_amount,
                    'total_cost': total_cost,
                    'profit': total_profit
                }
            })
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'创建销售订单失败: {str(e)}'
        }), 500

@sales_bp.route('/api/outgoing-orders/<int:order_id>', methods=['DELETE'])
@login_required
def delete_outgoing_order(order_id):
    """删除销售订单（退货）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查订单是否存在
        cursor.execute("SELECT id FROM outgoing_orders WHERE id = %s", (order_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '销售订单不存在'
            })
        
        try:
            # 获取订单明细用于恢复库存
            cursor.execute("""
                SELECT product_id, quantity 
                FROM outgoing_details 
                WHERE outgoing_id = %s
            """, (order_id,))
            details = cursor.fetchall()
            
            # 恢复库存
            for detail in details:
                cursor.execute("""
                    UPDATE inventory 
                    SET quantity = quantity + %s, updated_at = NOW()
                    WHERE product_id = %s
                """, (detail[1], detail[0]))  # quantity, product_id
            
            # 删除销售明细
            cursor.execute("DELETE FROM outgoing_details WHERE outgoing_id = %s", (order_id,))
            
            # 删除销售订单
            cursor.execute("DELETE FROM outgoing_orders WHERE id = %s", (order_id,))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': '销售订单删除成功，库存已恢复'
            })
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除销售订单失败: {str(e)}'
        }), 500

@sales_bp.route('/api/sales/daily-summary', methods=['GET'])
@login_required
def get_daily_sales_summary():
    """获取每日销售汇总"""
    try:
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        conn = get_db_dict_connection()
        cursor = conn.cursor()
        
        # 获取当日销售汇总
        cursor.execute("""
            SELECT 
                COUNT(*) as order_count,
                COALESCE(SUM(total_amount), 0) as total_sales,
                COALESCE(SUM(total_cost), 0) as total_cost,
                COALESCE(SUM(profit), 0) as total_profit
            FROM outgoing_orders
            WHERE sale_date = %s
        """, (date,))
        
        summary = cursor.fetchone()
        
        # 获取商品销售排行
        cursor.execute("""
            SELECT p.name, p.unit, SUM(od.quantity) as total_quantity,
                   SUM(od.amount) as total_amount, SUM(od.profit) as total_profit
            FROM outgoing_details od
            INNER JOIN outgoing_orders oo ON od.outgoing_id = oo.id
            INNER JOIN products p ON od.product_id = p.id
            WHERE oo.sale_date = %s
            GROUP BY od.product_id, p.name, p.unit
            ORDER BY total_amount DESC
            LIMIT 10
        """, (date,))
        
        top_products = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # 格式化数据
        summary['total_sales'] = float(summary['total_sales'])
        summary['total_cost'] = float(summary['total_cost'])
        summary['total_profit'] = float(summary['total_profit'])
        
        for product in top_products:
            product['total_amount'] = float(product['total_amount'])
            product['total_profit'] = float(product['total_profit'])
        
        return jsonify({
            'success': True,
            'data': {
                'date': date,
                'summary': summary,
                'top_products': top_products
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取销售汇总失败: {str(e)}'
        }), 500