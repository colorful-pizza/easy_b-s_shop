from flask import render_template, abort
from . import printing_bp
from utils.database import get_db_dict_connection
from utils.auth import login_required
from utils.helpers import format_datetime, format_date


@printing_bp.route('/printing/purchase/apply/<int:order_id>')
@login_required
def print_purchase_apply(order_id: int):
    """打印采购申请单（pending）"""
    try:
        conn = get_db_dict_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT po.id, po.order_no, po.status, po.supplier_id, s.name as supplier_name,
                   po.total_amount, po.apply_user_id, u1.real_name as apply_user_name,
                   po.apply_time, po.remark
            FROM purchase_orders po
            LEFT JOIN suppliers s ON po.supplier_id = s.id
            LEFT JOIN users u1 ON po.apply_user_id = u1.id
            WHERE po.id = %s
            """,
            (order_id,),
        )
        order = cursor.fetchone()
        if not order or order['status'] != 'pending':
            abort(404)
        cursor.execute(
            """
            SELECT pd.id, pd.product_id, p.code, p.name as product_name, p.unit,
                   pd.quantity, pd.cost_price, pd.amount
            FROM purchase_details pd
            LEFT JOIN products p ON pd.product_id = p.id
            WHERE pd.purchase_id = %s
            ORDER BY pd.id
            """,
            (order_id,),
        )
        details = cursor.fetchall()
        cursor.close()
        conn.close()
        # 格式化
        order['apply_time'] = format_datetime(order['apply_time'])
        order['total_amount'] = float(order['total_amount'] or 0)
        for d in details:
            d['cost_price'] = float(d['cost_price'] or 0)
            d['amount'] = float(d['amount'] or 0)
        return render_template('printing/purchase_apply.html', order=order, details=details)
    except Exception:
        abort(500)


@printing_bp.route('/printing/purchase/order/<int:order_id>')
@login_required
def print_purchase_order(order_id: int):
    """打印采购订单（approved）"""
    try:
        conn = get_db_dict_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT po.id, po.order_no, po.status, po.supplier_id, s.name as supplier_name,
                   po.total_amount, po.apply_user_id, u1.real_name as apply_user_name,
                   po.approve_user_id, u2.real_name as approve_user_name,
                   po.apply_time, po.approve_time, po.remark
            FROM purchase_orders po
            LEFT JOIN suppliers s ON po.supplier_id = s.id
            LEFT JOIN users u1 ON po.apply_user_id = u1.id
            LEFT JOIN users u2 ON po.approve_user_id = u2.id
            WHERE po.id = %s
            """,
            (order_id,),
        )
        order = cursor.fetchone()
        if not order or order['status'] != 'approved':
            abort(404)
        cursor.execute(
            """
            SELECT pd.id, pd.product_id, p.code, p.name as product_name, p.unit,
                   pd.quantity, pd.cost_price, pd.amount
            FROM purchase_details pd
            LEFT JOIN products p ON pd.product_id = p.id
            WHERE pd.purchase_id = %s
            ORDER BY pd.id
            """,
            (order_id,),
        )
        details = cursor.fetchall()
        cursor.close()
        conn.close()
        # 格式化
        order['apply_time'] = format_datetime(order['apply_time'])
        order['approve_time'] = format_datetime(order['approve_time'])
        order['total_amount'] = float(order['total_amount'] or 0)
        for d in details:
            d['cost_price'] = float(d['cost_price'] or 0)
            d['amount'] = float(d['amount'] or 0)
        return render_template('printing/purchase_order.html', order=order, details=details)
    except Exception:
        abort(500)
