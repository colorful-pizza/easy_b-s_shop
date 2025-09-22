from flask import render_template, abort
from . import printing_bp
from utils.database import get_db_dict_connection
from utils.auth import login_required
from utils.helpers import format_datetime, format_date


@printing_bp.route('/printing/receipt/<int:order_id>')
@login_required
def print_receipt(order_id: int):
    try:
        conn = get_db_dict_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT oo.id, oo.order_no, oo.customer_id, c.name as customer_name,
                   oo.total_amount, oo.total_cost, oo.profit,
                   oo.sale_date, oo.user_id, u.real_name as user_name,
                   oo.created_at, oo.remark
            FROM outgoing_orders oo
            LEFT JOIN customers c ON oo.customer_id = c.id
            LEFT JOIN users u ON oo.user_id = u.id
            WHERE oo.id = %s
            """,
            (order_id,),
        )
        order = cursor.fetchone()
        if not order:
            abort(404)

        cursor.execute(
            """
            SELECT od.id, od.product_id, p.code, p.name as product_name, p.unit,
                   od.quantity, od.selling_price, od.cost_price,
                   od.amount, od.cost_amount, od.profit
            FROM outgoing_details od
            LEFT JOIN products p ON od.product_id = p.id
            WHERE od.outgoing_id = %s
            ORDER BY od.id
            """,
            (order_id,),
        )
        details = cursor.fetchall()

        cursor.close()
        conn.close()

        # 格式化
        order['sale_date'] = format_date(order['sale_date'])
        order['created_at'] = format_datetime(order['created_at'])
        order['total_amount'] = float(order['total_amount'] or 0)
        order['total_cost'] = float(order['total_cost'] or 0)
        order['profit'] = float(order['profit'] or 0)
        for d in details:
            d['selling_price'] = float(d['selling_price'] or 0)
            d['amount'] = float(d['amount'] or 0)

        return render_template('printing/receipt.html', order=order, details=details)
    except Exception:
        abort(500)
