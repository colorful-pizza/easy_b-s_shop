from flask import render_template, abort
from . import printing_bp
from utils.database import get_db_dict_connection
from utils.auth import login_required
from utils.helpers import format_datetime, format_date


@printing_bp.route('/printing/stockcheck/sheet/<int:check_id>')
@login_required
def print_stockcheck_sheet(check_id: int):
    """打印库存盘点单（实际数留空，供线下填写）"""
    try:
        conn = get_db_dict_connection()
        cursor = conn.cursor()

        # 盘点基本信息
        cursor.execute(
            """
            SELECT ic.id, ic.check_no, ic.check_date, ic.status, ic.total_difference,
                   ic.user_id, u.real_name AS user_name, ic.created_at, ic.remark
            FROM inventory_checks ic
            LEFT JOIN users u ON ic.user_id = u.id
            WHERE ic.id = %s
            """,
            (check_id,),
        )
        check = cursor.fetchone()
        if not check:
            abort(404)

        # 明细（不限制状态，打印时“实际数”列不显示数据库值）
        cursor.execute(
            """
            SELECT icd.id, icd.product_id, p.code, p.name AS product_name, p.unit,
                   icd.book_quantity
            FROM inventory_check_details icd
            LEFT JOIN products p ON icd.product_id = p.id
            WHERE icd.check_id = %s
            ORDER BY p.code
            """,
            (check_id,),
        )
        details = cursor.fetchall()

        cursor.close()
        conn.close()

        # 格式化
        check['check_date'] = format_date(check['check_date'])
        check['created_at'] = format_datetime(check['created_at'])

        return render_template(
            'printing/stockcheck_sheet.html',
            check=check,
            details=details or [],
        )
    except Exception:
        abort(500)
