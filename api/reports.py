"""
报表统计API模块
"""
from flask import Blueprint, request, jsonify
from utils.database import get_db_connection, get_db_dict_connection
from utils.auth import login_required, manager_required
from utils.helpers import format_date, safe_float
from datetime import datetime, timedelta

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/api/reports/dashboard', methods=['GET'])
@login_required
def get_dashboard_data():
    """获取仪表盘数据"""
    try:
        conn = get_db_dict_connection()
        cursor = conn.cursor()
        
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        this_month_start = today.replace(day=1)
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
        last_month_end = this_month_start - timedelta(days=1)
        
        # 今日销售统计
        cursor.execute("""
            SELECT 
                COUNT(*) as order_count,
                COALESCE(SUM(total_amount), 0) as total_sales,
                COALESCE(SUM(profit), 0) as total_profit
            FROM outgoing_orders
            WHERE sale_date = %s
        """, (today,))
        today_sales = cursor.fetchone()
        
        # 昨日销售统计
        cursor.execute("""
            SELECT 
                COUNT(*) as order_count,
                COALESCE(SUM(total_amount), 0) as total_sales,
                COALESCE(SUM(profit), 0) as total_profit
            FROM outgoing_orders
            WHERE sale_date = %s
        """, (yesterday,))
        yesterday_sales = cursor.fetchone()
        
        # 本月销售统计
        cursor.execute("""
            SELECT 
                COUNT(*) as order_count,
                COALESCE(SUM(total_amount), 0) as total_sales,
                COALESCE(SUM(profit), 0) as total_profit
            FROM outgoing_orders
            WHERE sale_date >= %s AND sale_date <= %s
        """, (this_month_start, today))
        this_month_sales = cursor.fetchone()
        
        # 上月销售统计
        cursor.execute("""
            SELECT 
                COUNT(*) as order_count,
                COALESCE(SUM(total_amount), 0) as total_sales,
                COALESCE(SUM(profit), 0) as total_profit
            FROM outgoing_orders
            WHERE sale_date >= %s AND sale_date <= %s
        """, (last_month_start, last_month_end))
        last_month_sales = cursor.fetchone()
        
        # 库存预警统计
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN COALESCE(i.quantity, 0) = 0 THEN 1 END) as zero_stock,
                COUNT(CASE WHEN COALESCE(i.quantity, 0) > 0 AND COALESCE(i.quantity, 0) <= 10 THEN 1 END) as low_stock,
                COALESCE(SUM(i.quantity * p.selling_price), 0) as total_inventory_value
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            WHERE p.status = 'active'
        """)
        inventory_stats = cursor.fetchone()
        
        # 最近7天销售趋势
        cursor.execute("""
            SELECT 
                sale_date,
                COUNT(*) as order_count,
                COALESCE(SUM(total_amount), 0) as total_sales,
                COALESCE(SUM(profit), 0) as total_profit
            FROM outgoing_orders
            WHERE sale_date >= %s AND sale_date <= %s
            GROUP BY sale_date
            ORDER BY sale_date
        """, (today - timedelta(days=6), today))
        sales_trend = cursor.fetchall()
        
        # 热销商品Top 10
        cursor.execute("""
            SELECT p.name, p.unit, SUM(od.quantity) as total_quantity,
                   SUM(od.amount) as total_sales, SUM(od.profit) as total_profit
            FROM outgoing_details od
            INNER JOIN outgoing_orders oo ON od.outgoing_id = oo.id
            INNER JOIN products p ON od.product_id = p.id
            WHERE oo.sale_date >= %s
            GROUP BY od.product_id, p.name, p.unit
            ORDER BY total_sales DESC
            LIMIT 10
        """, (this_month_start,))
        top_products = cursor.fetchall()

        # 待处理订单（采购单：待定/已批准）
        cursor.execute("""
            SELECT COUNT(*) AS pending_count
            FROM purchase_orders
            WHERE status IN ('pending','approved')
        """)
        pending_row = cursor.fetchone()
        pending_orders = int(pending_row['pending_count']) if pending_row and 'pending_count' in pending_row else 0
        
        cursor.close()
        conn.close()
        
        # 格式化数据
        for item in [today_sales, yesterday_sales, this_month_sales, last_month_sales]:
            item['total_sales'] = float(item['total_sales'])
            item['total_profit'] = float(item['total_profit'])
        
        inventory_stats['total_inventory_value'] = float(inventory_stats['total_inventory_value'])
        
        for item in sales_trend:
            item['sale_date'] = format_date(item['sale_date'])
            item['total_sales'] = float(item['total_sales'])
            item['total_profit'] = float(item['total_profit'])
        
        for item in top_products:
            item['total_sales'] = float(item['total_sales'])
            item['total_profit'] = float(item['total_profit'])
        
        return jsonify({
            'success': True,
            'data': {
                'today_sales': today_sales,
                'yesterday_sales': yesterday_sales,
                'this_month_sales': this_month_sales,
                'last_month_sales': last_month_sales,
                'inventory_stats': inventory_stats,
                'sales_trend': sales_trend,
                'top_products': top_products,
                'pending_orders': pending_orders
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取仪表盘数据失败: {str(e)}'
        }), 500

@reports_bp.route('/api/reports/sales', methods=['GET'])
@login_required
def get_sales_report():
    """获取销售报表"""
    try:
        start_date = request.args.get('start_date', '').strip()
        end_date = request.args.get('end_date', '').strip()
        group_by = request.args.get('group_by', 'day')  # day, week, month
        
        if not start_date or not end_date:
            return jsonify({
                'success': False,
                'message': '请指定开始日期和结束日期'
            })
        
        conn = get_db_dict_connection()
        cursor = conn.cursor()
        
        # 根据分组方式构建查询
        if group_by == 'day':
            date_format = '%Y-%m-%d'
            group_field = 'sale_date'
        elif group_by == 'week':
            date_format = '%Y-%u'
            group_field = 'YEARWEEK(sale_date, 1)'
        elif group_by == 'month':
            date_format = '%Y-%m'
            group_field = 'DATE_FORMAT(sale_date, "%Y-%m")'
        else:
            date_format = '%Y-%m-%d'
            group_field = 'sale_date'
        
        # 销售统计
        cursor.execute(f"""
            SELECT 
                {group_field} as period,
                COUNT(*) as order_count,
                COALESCE(SUM(total_amount), 0) as total_sales,
                COALESCE(SUM(total_cost), 0) as total_cost,
                COALESCE(SUM(profit), 0) as total_profit,
                ROUND(COALESCE(SUM(profit) / SUM(total_amount) * 100, 0), 2) as profit_rate
            FROM outgoing_orders
            WHERE sale_date >= %s AND sale_date <= %s
            GROUP BY {group_field}
            ORDER BY period
        """, (start_date, end_date))
        
        sales_data = cursor.fetchall()
        
        # 总计
        cursor.execute("""
            SELECT 
                COUNT(*) as total_orders,
                COALESCE(SUM(total_amount), 0) as total_sales,
                COALESCE(SUM(total_cost), 0) as total_cost,
                COALESCE(SUM(profit), 0) as total_profit,
                ROUND(COALESCE(SUM(profit) / SUM(total_amount) * 100, 0), 2) as profit_rate
            FROM outgoing_orders
            WHERE sale_date >= %s AND sale_date <= %s
        """, (start_date, end_date))
        
        summary = cursor.fetchone()
        
        # 商品销售排行
        cursor.execute("""
            SELECT p.name, p.unit, SUM(od.quantity) as total_quantity,
                   SUM(od.amount) as total_sales, SUM(od.profit) as total_profit,
                   ROUND(SUM(od.profit) / SUM(od.amount) * 100, 2) as profit_rate
            FROM outgoing_details od
            INNER JOIN outgoing_orders oo ON od.outgoing_id = oo.id
            INNER JOIN products p ON od.product_id = p.id
            WHERE oo.sale_date >= %s AND oo.sale_date <= %s
            GROUP BY od.product_id, p.name, p.unit
            ORDER BY total_sales DESC
            LIMIT 20
        """, (start_date, end_date))
        
        product_ranking = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # 格式化数据
        for item in sales_data:
            item['total_sales'] = float(item['total_sales'])
            item['total_cost'] = float(item['total_cost'])
            item['total_profit'] = float(item['total_profit'])
        
        summary['total_sales'] = float(summary['total_sales'])
        summary['total_cost'] = float(summary['total_cost'])
        summary['total_profit'] = float(summary['total_profit'])
        
        for item in product_ranking:
            item['total_sales'] = float(item['total_sales'])
            item['total_profit'] = float(item['total_profit'])
        
        return jsonify({
            'success': True,
            'data': {
                'period': f'{start_date} 至 {end_date}',
                'group_by': group_by,
                'sales_data': sales_data,
                'summary': summary,
                'product_ranking': product_ranking
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取销售报表失败: {str(e)}'
        }), 500

@reports_bp.route('/api/reports/purchase', methods=['GET'])
@login_required
def get_purchase_report():
    """获取采购报表"""
    try:
        start_date = request.args.get('start_date', '').strip()
        end_date = request.args.get('end_date', '').strip()
        
        if not start_date or not end_date:
            return jsonify({
                'success': False,
                'message': '请指定开始日期和结束日期'
            })
        
        conn = get_db_dict_connection()
        cursor = conn.cursor()
        
        # 采购申请统计
        cursor.execute("""
            SELECT 
                status,
                COUNT(*) as count,
                COALESCE(SUM(total_amount), 0) as total_amount
            FROM purchase_orders
            WHERE DATE(apply_time) >= %s AND DATE(apply_time) <= %s
            GROUP BY status
        """, (start_date, end_date))
        
        purchase_orders_stats = cursor.fetchall()
        
        # 进货统计
        cursor.execute("""
            SELECT 
                incoming_date,
                COUNT(*) as order_count,
                COALESCE(SUM(total_amount), 0) as total_amount
            FROM incoming_orders
            WHERE incoming_date >= %s AND incoming_date <= %s
            GROUP BY incoming_date
            ORDER BY incoming_date
        """, (start_date, end_date))
        
        incoming_data = cursor.fetchall()
        
        # 供应商采购排行
        cursor.execute("""
            SELECT s.name as supplier_name,
                   COUNT(io.id) as order_count,
                   COALESCE(SUM(io.total_amount), 0) as total_amount
            FROM incoming_orders io
            INNER JOIN suppliers s ON io.supplier_id = s.id
            WHERE io.incoming_date >= %s AND io.incoming_date <= %s
            GROUP BY io.supplier_id, s.name
            ORDER BY total_amount DESC
            LIMIT 10
        """, (start_date, end_date))
        
        supplier_ranking = cursor.fetchall()
        
        # 商品进货排行
        cursor.execute("""
            SELECT p.name, p.unit, SUM(id.quantity) as total_quantity,
                   SUM(id.amount) as total_amount
            FROM incoming_details id
            INNER JOIN incoming_orders io ON id.incoming_id = io.id
            INNER JOIN products p ON id.product_id = p.id
            WHERE io.incoming_date >= %s AND io.incoming_date <= %s
            GROUP BY id.product_id, p.name, p.unit
            ORDER BY total_amount DESC
            LIMIT 20
        """, (start_date, end_date))
        
        product_ranking = cursor.fetchall()
        
        # 总计
        cursor.execute("""
            SELECT 
                COUNT(*) as total_incoming_orders,
                COALESCE(SUM(total_amount), 0) as total_incoming_amount
            FROM incoming_orders
            WHERE incoming_date >= %s AND incoming_date <= %s
        """, (start_date, end_date))
        
        summary = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        # 格式化数据
        for item in purchase_orders_stats:
            item['total_amount'] = float(item['total_amount'])
        
        for item in incoming_data:
            item['incoming_date'] = format_date(item['incoming_date'])
            item['total_amount'] = float(item['total_amount'])
        
        for item in supplier_ranking:
            item['total_amount'] = float(item['total_amount'])
        
        for item in product_ranking:
            item['total_amount'] = float(item['total_amount'])
        
        summary['total_incoming_amount'] = float(summary['total_incoming_amount'])
        
        return jsonify({
            'success': True,
            'data': {
                'period': f'{start_date} 至 {end_date}',
                'purchase_orders_stats': purchase_orders_stats,
                'incoming_data': incoming_data,
                'supplier_ranking': supplier_ranking,
                'product_ranking': product_ranking,
                'summary': summary
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取采购报表失败: {str(e)}'
        }), 500

@reports_bp.route('/api/reports/inventory', methods=['GET'])
@login_required
def get_inventory_report():
    """获取库存报表"""
    try:
        conn = get_db_dict_connection()
        cursor = conn.cursor()
        
        # 库存总览
        cursor.execute("""
            SELECT 
                COUNT(p.id) as total_products,
                COUNT(CASE WHEN COALESCE(i.quantity, 0) > 0 THEN 1 END) as in_stock_products,
                COUNT(CASE WHEN COALESCE(i.quantity, 0) = 0 THEN 1 END) as out_of_stock_products,
                COUNT(CASE WHEN COALESCE(i.quantity, 0) > 0 AND COALESCE(i.quantity, 0) <= 10 THEN 1 END) as low_stock_products,
                COALESCE(SUM(i.quantity), 0) as total_quantity,
                COALESCE(SUM(i.quantity * p.selling_price), 0) as total_value
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            WHERE p.status = 'active'
        """)
        overview = cursor.fetchone()
        
        # 按分类统计
        cursor.execute("""
            SELECT 
                COALESCE(p.category, '未分类') as category,
                COUNT(p.id) as product_count,
                COALESCE(SUM(i.quantity), 0) as total_quantity,
                COALESCE(SUM(i.quantity * p.selling_price), 0) as total_value
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            WHERE p.status = 'active'
            GROUP BY p.category
            ORDER BY total_value DESC
        """)
        by_category = cursor.fetchall()
        
        # 零库存商品
        cursor.execute("""
            SELECT p.code, p.name, p.category, p.brand, p.selling_price
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            WHERE p.status = 'active' AND COALESCE(i.quantity, 0) = 0
            ORDER BY p.category, p.name
            LIMIT 50
        """)
        zero_stock = cursor.fetchall()
        
        # 低库存商品
        cursor.execute("""
            SELECT p.code, p.name, p.category, p.brand, 
                   COALESCE(i.quantity, 0) as quantity, p.selling_price
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            WHERE p.status = 'active' 
              AND COALESCE(i.quantity, 0) > 0 
              AND COALESCE(i.quantity, 0) <= 10
            ORDER BY i.quantity, p.name
            LIMIT 50
        """)
        low_stock = cursor.fetchall()
        
        # 高价值库存
        cursor.execute("""
            SELECT p.code, p.name, p.category, p.brand, 
                   COALESCE(i.quantity, 0) as quantity, p.selling_price,
                   COALESCE(i.quantity * p.selling_price, 0) as total_value
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            WHERE p.status = 'active' AND COALESCE(i.quantity, 0) > 0
            ORDER BY total_value DESC
            LIMIT 20
        """)
        high_value = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # 格式化数据
        overview['total_value'] = float(overview['total_value'])
        
        for item in by_category:
            item['total_value'] = float(item['total_value'])
        
        for item in zero_stock:
            item['selling_price'] = float(item['selling_price'])
        
        for item in low_stock:
            item['selling_price'] = float(item['selling_price'])
        
        for item in high_value:
            item['selling_price'] = float(item['selling_price'])
            item['total_value'] = float(item['total_value'])
        
        return jsonify({
            'success': True,
            'data': {
                'overview': overview,
                'by_category': by_category,
                'zero_stock': zero_stock,
                'low_stock': low_stock,
                'high_value': high_value
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取库存报表失败: {str(e)}'
        }), 500

@reports_bp.route('/api/reports/profit', methods=['GET'])
@login_required
@manager_required
def get_profit_report():
    """获取利润报表"""
    try:
        start_date = request.args.get('start_date', '').strip()
        end_date = request.args.get('end_date', '').strip()
        group_by = request.args.get('group_by', 'day')  # day, week, month
        
        if not start_date or not end_date:
            return jsonify({
                'success': False,
                'message': '请指定开始日期和结束日期'
            })
        
        conn = get_db_dict_connection()
        cursor = conn.cursor()
        
        # 根据分组方式构建查询
        if group_by == 'day':
            group_field = 'sale_date'
        elif group_by == 'week':
            group_field = 'YEARWEEK(sale_date, 1)'
        elif group_by == 'month':
            group_field = 'DATE_FORMAT(sale_date, "%Y-%m")'
        else:
            group_field = 'sale_date'
        
        # 利润统计
        cursor.execute(f"""
            SELECT 
                {group_field} as period,
                COALESCE(SUM(total_amount), 0) as total_sales,
                COALESCE(SUM(total_cost), 0) as total_cost,
                COALESCE(SUM(profit), 0) as total_profit,
                ROUND(COALESCE(SUM(profit) / SUM(total_amount) * 100, 0), 2) as profit_rate
            FROM outgoing_orders
            WHERE sale_date >= %s AND sale_date <= %s
            GROUP BY {group_field}
            ORDER BY period
        """, (start_date, end_date))
        
        profit_data = cursor.fetchall()
        
        # 商品利润排行
        cursor.execute("""
            SELECT p.name, p.unit, 
                   SUM(od.quantity) as total_quantity,
                   SUM(od.amount) as total_sales,
                   SUM(od.cost_amount) as total_cost,
                   SUM(od.profit) as total_profit,
                   ROUND(SUM(od.profit) / SUM(od.amount) * 100, 2) as profit_rate
            FROM outgoing_details od
            INNER JOIN outgoing_orders oo ON od.outgoing_id = oo.id
            INNER JOIN products p ON od.product_id = p.id
            WHERE oo.sale_date >= %s AND oo.sale_date <= %s
            GROUP BY od.product_id, p.name, p.unit
            HAVING total_profit > 0
            ORDER BY total_profit DESC
            LIMIT 20
        """, (start_date, end_date))
        
        product_profit = cursor.fetchall()
        
        # 总计
        cursor.execute("""
            SELECT 
                COALESCE(SUM(total_amount), 0) as total_sales,
                COALESCE(SUM(total_cost), 0) as total_cost,
                COALESCE(SUM(profit), 0) as total_profit,
                ROUND(COALESCE(SUM(profit) / SUM(total_amount) * 100, 0), 2) as profit_rate
            FROM outgoing_orders
            WHERE sale_date >= %s AND sale_date <= %s
        """, (start_date, end_date))
        
        summary = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        # 格式化数据
        for item in profit_data:
            item['total_sales'] = float(item['total_sales'])
            item['total_cost'] = float(item['total_cost'])
            item['total_profit'] = float(item['total_profit'])
        
        for item in product_profit:
            item['total_sales'] = float(item['total_sales'])
            item['total_cost'] = float(item['total_cost'])
            item['total_profit'] = float(item['total_profit'])
        
        summary['total_sales'] = float(summary['total_sales'])
        summary['total_cost'] = float(summary['total_cost'])
        summary['total_profit'] = float(summary['total_profit'])
        
        return jsonify({
            'success': True,
            'data': {
                'period': f'{start_date} 至 {end_date}',
                'group_by': group_by,
                'profit_data': profit_data,
                'product_profit': product_profit,
                'summary': summary
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取利润报表失败: {str(e)}'
        }), 500