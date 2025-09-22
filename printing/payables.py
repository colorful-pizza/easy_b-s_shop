from flask import render_template, abort
from . import printing_bp
from utils.database import get_db_dict_connection
from utils.auth import login_required
from utils.helpers import format_datetime


@printing_bp.route('/printing/payables/statement/<int:supplier_id>')
@login_required
def print_supplier_statement(supplier_id: int):
    """打印供应商应付对账单（未结算：delivered/stock）"""
    try:
        conn = get_db_dict_connection()
        cursor = conn.cursor()

        # 供应商信息
        cursor.execute(
            """
            SELECT id, name, contact_person, phone, address
            FROM suppliers
            WHERE id = %s
            """,
            (supplier_id,),
        )
        supplier = cursor.fetchone()
        if not supplier:
            abort(404)

        # 未结算订单
        cursor.execute(
            """
            SELECT po.id, po.order_no, po.status, po.total_amount,
                   po.apply_time, po.approve_time
            FROM purchase_orders po
            WHERE po.supplier_id = %s AND po.status IN ('delivered','stock')
            ORDER BY po.apply_time DESC
            """,
            (supplier_id,),
        )
        orders = cursor.fetchall()

        details = []
        if orders:
            purchase_ids = [o['id'] for o in orders]
            cursor.execute(
                f"""
                SELECT pd.id, pd.purchase_id, pd.product_id, p.code, p.name AS product_name, p.unit,
                       pd.quantity, pd.cost_price, pd.amount
                FROM purchase_details pd
                JOIN products p ON pd.product_id = p.id
                WHERE pd.purchase_id IN ({', '.join(['%s']*len(purchase_ids))})
                ORDER BY pd.purchase_id, pd.id
                """,
                purchase_ids,
            )
            details = cursor.fetchall()

        cursor.close()
        conn.close()

        # 格式化
        total_amount = 0.0
        for o in orders or []:
            o['total_amount'] = float(o['total_amount'] or 0)
            o['apply_time'] = format_datetime(o['apply_time'])
            o['approve_time'] = format_datetime(o['approve_time'])
            total_amount += o['total_amount']
        for d in details or []:
            d['cost_price'] = float(d['cost_price'] or 0)
            d['amount'] = float(d['amount'] or 0)

        return render_template(
            'printing/supplier_statement.html',
            supplier=supplier,
            orders=orders or [],
            details=details or [],
            total_amount=total_amount,
        )
    except Exception:
        abort(500)
