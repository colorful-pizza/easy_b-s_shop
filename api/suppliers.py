"""
供应商管理API模块
"""
from flask import Blueprint, request, jsonify
from utils.database import get_db_connection, get_db_dict_connection
from utils.auth import login_required, manager_required
from utils.helpers import validate_required_fields, validate_phone, format_datetime

suppliers_bp = Blueprint('suppliers', __name__)

@suppliers_bp.route('/api/suppliers', methods=['GET'])
@login_required
def get_suppliers():
    """获取供应商列表（分页）"""
    try:
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 10))
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '').strip()
        
        conn = get_db_dict_connection()
        cursor = conn.cursor()
        
        # 构建查询条件
        where_conditions = []
        params = []
        
        if search:
            where_conditions.append("(name LIKE %s OR contact_person LIKE %s)")
            params.extend([f'%{search}%', f'%{search}%'])
        
        if status:
            where_conditions.append("status = %s")
            params.append(status)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # 计数查询
        count_query = f"SELECT COUNT(*) FROM suppliers {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['COUNT(*)']
        
        # 数据查询
        offset = (page - 1) * size
        data_query = f"""
            SELECT id, name, contact_person, phone, address, status, created_at, remark
            FROM suppliers 
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(data_query, params + [size, offset])
        suppliers = cursor.fetchall()
        
        # 格式化数据
        for supplier in suppliers:
            supplier['created_at'] = format_datetime(supplier['created_at'])
        
        cursor.close()
        conn.close()
        
        # 计算分页信息
        total_pages = (total + size - 1) // size
        
        return jsonify({
            'success': True,
            'data': suppliers,
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
            'message': f'获取供应商列表失败: {str(e)}'
        }), 500

@suppliers_bp.route('/api/suppliers/<int:supplier_id>', methods=['GET'])
@login_required
def get_supplier(supplier_id):
    """获取供应商详情"""
    try:
        conn = get_db_dict_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, contact_person, phone, address, status, created_at, remark
            FROM suppliers
            WHERE id = %s
        """, (supplier_id,))
        
        supplier = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not supplier:
            return jsonify({
                'success': False,
                'message': '供应商不存在'
            }), 404
        
        # 格式化数据
        supplier['created_at'] = format_datetime(supplier['created_at'])
        
        return jsonify({
            'success': True,
            'data': supplier
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取供应商详情失败: {str(e)}'
        }), 500

@suppliers_bp.route('/api/suppliers', methods=['POST'])
@login_required
@manager_required
def create_supplier():
    """创建供应商"""
    try:
        data = request.get_json() or {}
        
        # 验证必填字段
        required_fields = ['name']
        is_valid, message = validate_required_fields(data, required_fields)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': message
            })
        
        name = data['name'].strip()
        contact_person = data.get('contact_person', '').strip()
        phone = data.get('phone', '').strip()
        address = data.get('address', '').strip()
        remark = data.get('remark', '').strip()
        
        # 验证手机号
        if phone and not validate_phone(phone):
            return jsonify({
                'success': False,
                'message': '手机号格式不正确'
            })
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查供应商名称是否重复
        cursor.execute("SELECT id FROM suppliers WHERE name = %s", (name,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '供应商名称已存在'
            })
        
        # 插入供应商
        cursor.execute("""
            INSERT INTO suppliers (name, contact_person, phone, address, remark)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, contact_person or None, phone or None, address or None, remark or None))
        
        supplier_id = cursor.lastrowid
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '供应商创建成功',
            'data': {'supplier_id': supplier_id}
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'创建供应商失败: {str(e)}'
        }), 500

@suppliers_bp.route('/api/suppliers/<int:supplier_id>', methods=['PUT'])
@login_required
@manager_required
def update_supplier(supplier_id):
    """更新供应商信息"""
    try:
        data = request.get_json() or {}
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查供应商是否存在
        cursor.execute("SELECT id FROM suppliers WHERE id = %s", (supplier_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '供应商不存在'
            })
        
        # 构建更新字段
        update_fields = []
        params = []
        
        if 'name' in data:
            name = data['name'].strip()
            if not name:
                cursor.close()
                conn.close()
                return jsonify({
                    'success': False,
                    'message': '供应商名称不能为空'
                })
            
            # 检查名称重复
            cursor.execute("SELECT id FROM suppliers WHERE name = %s AND id != %s", (name, supplier_id))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return jsonify({
                    'success': False,
                    'message': '供应商名称已存在'
                })
            
            update_fields.append("name = %s")
            params.append(name)
        
        if 'contact_person' in data:
            update_fields.append("contact_person = %s")
            params.append(data['contact_person'].strip() or None)
        
        if 'phone' in data:
            phone = data['phone'].strip()
            if phone and not validate_phone(phone):
                cursor.close()
                conn.close()
                return jsonify({
                    'success': False,
                    'message': '手机号格式不正确'
                })
            update_fields.append("phone = %s")
            params.append(phone or None)
        
        if 'address' in data:
            update_fields.append("address = %s")
            params.append(data['address'].strip() or None)
        
        if 'status' in data:
            status = data['status'].strip()
            if status not in ['active', 'inactive']:
                cursor.close()
                conn.close()
                return jsonify({
                    'success': False,
                    'message': '状态只能是active或inactive'
                })
            update_fields.append("status = %s")
            params.append(status)
        
        if 'remark' in data:
            update_fields.append("remark = %s")
            params.append(data['remark'].strip() or None)
        
        if not update_fields:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '没有需要更新的字段'
            })
        
        # 执行更新
        params.append(supplier_id)
        update_sql = f"UPDATE suppliers SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(update_sql, params)
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '供应商信息更新成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'更新供应商失败: {str(e)}'
        }), 500

@suppliers_bp.route('/api/suppliers/<int:supplier_id>', methods=['DELETE'])
@login_required
@manager_required
def delete_supplier(supplier_id):
    """删除供应商"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查供应商是否存在
        cursor.execute("SELECT id FROM suppliers WHERE id = %s", (supplier_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '供应商不存在'
            })
        
        # 检查是否有相关的业务数据
        cursor.execute("SELECT id FROM purchase_orders WHERE supplier_id = %s LIMIT 1", (supplier_id,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '供应商已有采购记录，不能删除'
            })
        
        cursor.execute("SELECT id FROM incoming_orders WHERE supplier_id = %s LIMIT 1", (supplier_id,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '供应商已有进货记录，不能删除'
            })
        
        # 删除供应商
        cursor.execute("DELETE FROM suppliers WHERE id = %s", (supplier_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '供应商删除成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除供应商失败: {str(e)}'
        }), 500

@suppliers_bp.route('/api/suppliers/search', methods=['GET'])
@login_required
def search_suppliers():
    """搜索供应商（用于选择器）"""
    try:
        keyword = request.args.get('keyword', '').strip()
        limit = int(request.args.get('limit', 20))
        
        conn = get_db_dict_connection()
        cursor = conn.cursor()
        
        where_clause = "WHERE status = 'active'"
        params = []
        
        if keyword:
            where_clause += " AND (name LIKE %s OR contact_person LIKE %s)"
            params.extend([f'%{keyword}%', f'%{keyword}%'])
        
        cursor.execute(f"""
            SELECT id, name, contact_person, phone, address
            FROM suppliers
            {where_clause}
            ORDER BY name
            LIMIT %s
        """, params + [limit])
        
        suppliers = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': suppliers
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'搜索供应商失败: {str(e)}'
        }), 500

# ==================== 供应商应付与结算 ====================

@suppliers_bp.route('/api/suppliers/payables', methods=['GET'])
@login_required
def get_suppliers_payables():
    """获取存在未付款采购单（delivered/stock）的供应商列表（分页汇总）"""
    try:
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 10))
        search = request.args.get('search', '').strip()

        conn = get_db_dict_connection()
        cursor = conn.cursor()

        where_conditions = ["s.status = 'active'"]
        params = []
        if search:
            where_conditions.append("(s.name LIKE %s OR s.contact_person LIKE %s)")
            params.extend([f'%{search}%', f'%{search}%'])
        where_clause = " AND ".join(where_conditions)

        # 计数（distinct 供应商）
        count_sql = f"""
            SELECT COUNT(*) FROM (
              SELECT s.id
              FROM suppliers s
              JOIN purchase_orders po ON po.supplier_id = s.id
                 AND po.status IN ('delivered','stock')
              WHERE {where_clause}
              GROUP BY s.id
            ) t
        """
        cursor.execute(count_sql, params)
        total = cursor.fetchone()['COUNT(*)']

        offset = (page - 1) * size
        data_sql = f"""
            SELECT s.id as supplier_id, s.name, s.contact_person, s.phone,
                   COUNT(po.id) as unpaid_count,
                   COALESCE(SUM(po.total_amount), 0) as unpaid_amount
            FROM suppliers s
            JOIN purchase_orders po ON po.supplier_id = s.id
               AND po.status IN ('delivered','stock')
            WHERE {where_clause}
            GROUP BY s.id, s.name, s.contact_person, s.phone
            ORDER BY unpaid_amount DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(data_sql, params + [size, offset])
        rows = cursor.fetchall()

        for r in rows:
            r['unpaid_amount'] = float(r['unpaid_amount'])

        cursor.close()
        conn.close()

        total_pages = (total + size - 1) // size
        return jsonify({
            'success': True,
            'data': rows,
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
        return jsonify({'success': False, 'message': f'获取应付供应商失败: {str(e)}'}), 500


@suppliers_bp.route('/api/suppliers/<int:supplier_id>/payables', methods=['GET'])
@login_required
def get_supplier_payable_orders(supplier_id):
    """获取指定供应商的未付款采购订单列表及明细"""
    try:
        conn = get_db_dict_connection()
        cursor = conn.cursor()

        # 供应商存在性
        cursor.execute("SELECT id, name FROM suppliers WHERE id = %s", (supplier_id,))
        sup = cursor.fetchone()
        if not sup:
            cursor.close(); conn.close()
            return jsonify({'success': False, 'message': '供应商不存在'}), 404

        # 订单列表
        cursor.execute(
            """
            SELECT po.id, po.order_no, po.status, po.total_amount,
                   po.apply_time, po.approve_time
            FROM purchase_orders po
            WHERE po.supplier_id = %s AND po.status IN ('delivered','stock')
            ORDER BY po.apply_time DESC
            """,
            (supplier_id,)
        )
        orders = cursor.fetchall()

        if not orders:
            cursor.close(); conn.close()
            return jsonify({'success': True, 'data': {'supplier': sup, 'orders': [], 'details': []}})

        purchase_ids = [o['id'] for o in orders]
        id_tuple = tuple(purchase_ids)
        # 明细一次性查询
        cursor.execute(
            f"""
            SELECT pd.id, pd.purchase_id, pd.product_id, p.code, p.name as product_name, p.unit,
                   pd.quantity, pd.cost_price, pd.amount, pd.remark
            FROM purchase_details pd
            JOIN products p ON pd.product_id = p.id
            WHERE pd.purchase_id IN ({', '.join(['%s']*len(purchase_ids))})
            ORDER BY pd.purchase_id, pd.id
            """,
            purchase_ids
        )
        details = cursor.fetchall()

        # 格式化金额
        for o in orders:
            o['total_amount'] = float(o['total_amount']) if o['total_amount'] else 0
            o['apply_time'] = format_datetime(o['apply_time'])
            o['approve_time'] = format_datetime(o['approve_time'])
        for d in details:
            d['cost_price'] = float(d['cost_price'])
            d['amount'] = float(d['amount'])

        cursor.close(); conn.close()
        return jsonify({'success': True, 'data': {'supplier': sup, 'orders': orders, 'details': details}})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取未付款订单失败: {str(e)}'}), 500


@suppliers_bp.route('/api/suppliers/<int:supplier_id>/settle', methods=['POST'])
@login_required
@manager_required
def settle_supplier_payables(supplier_id):
    """结算指定供应商的所有未付款（delivered/stock）采购订单，置为paid"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 统计待结算
        cursor.execute(
            """
            SELECT COUNT(*), COALESCE(SUM(total_amount), 0)
            FROM purchase_orders
            WHERE supplier_id = %s AND status IN ('delivered','stock')
            """,
            (supplier_id,)
        )
        row = cursor.fetchone()
        count_to_settle = row[0] if row else 0
        amount_to_settle = float(row[1] or 0)

        if count_to_settle == 0:
            cursor.close(); conn.close()
            return jsonify({'success': False, 'message': '没有可结算的订单'}), 400

        try:
            cursor.execute(
                """
                UPDATE purchase_orders
                SET status = 'paid'
                WHERE supplier_id = %s AND status IN ('delivered','stock')
                """,
                (supplier_id,)
            )
            conn.commit()
        except Exception as e:
            conn.rollback(); raise e
        finally:
            cursor.close(); conn.close()

        return jsonify({
            'success': True,
            'message': f'结算完成：{count_to_settle} 张订单，合计 ¥{amount_to_settle:.2f}',
            'data': {'count': count_to_settle, 'amount': amount_to_settle}
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'结算失败: {str(e)}'}), 500