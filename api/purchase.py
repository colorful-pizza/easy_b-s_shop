"""
采购管理API模块
"""
from flask import Blueprint, request, jsonify, session
from utils.database import get_db_connection, get_db_dict_connection
from utils.auth import login_required, manager_required, get_current_user
from utils.helpers import validate_required_fields, generate_order_no, format_datetime, format_date, safe_float, safe_int, safe_strip
from datetime import datetime

purchase_bp = Blueprint('purchase', __name__)

@purchase_bp.route('/api/purchase-orders', methods=['GET'])
@login_required
def get_purchase_orders():
    """获取采购申请列表（分页）"""
    try:
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 10))
        search = safe_strip(request.args.get('search'))
        status = safe_strip(request.args.get('status'))
        supplier_id = safe_strip(request.args.get('supplier_id'))
        
        conn = get_db_dict_connection()
        cursor = conn.cursor()
        
        # 构建查询条件
        where_conditions = []
        params = []
        
        if search:
            where_conditions.append("(po.order_no LIKE %s OR s.name LIKE %s OR u1.real_name LIKE %s)")
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
        
        if status:
            where_conditions.append("po.status = %s")
            params.append(status)
        
        if supplier_id:
            where_conditions.append("po.supplier_id = %s")
            params.append(supplier_id)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # 计数查询
        count_query = f"""
            SELECT COUNT(*) 
            FROM purchase_orders po
            LEFT JOIN suppliers s ON po.supplier_id = s.id
            LEFT JOIN users u1 ON po.apply_user_id = u1.id
            {where_clause}
        """
        cursor.execute(count_query, params)
        total = cursor.fetchone()['COUNT(*)']
        
        # 数据查询
        offset = (page - 1) * size
        data_query = f"""
            SELECT po.id, po.order_no, po.supplier_id, s.name as supplier_name,
                   po.status, po.total_amount, po.apply_user_id, u1.real_name as apply_user_name,
                   po.approve_user_id, u2.real_name as approve_user_name,
                   po.apply_time, po.approve_time, po.remark
            FROM purchase_orders po
            LEFT JOIN suppliers s ON po.supplier_id = s.id
            LEFT JOIN users u1 ON po.apply_user_id = u1.id
            LEFT JOIN users u2 ON po.approve_user_id = u2.id
            {where_clause}
            ORDER BY po.apply_time DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(data_query, params + [size, offset])
        orders = cursor.fetchall()
        
        # 格式化数据
        for order in orders:
            order['total_amount'] = float(order['total_amount']) if order['total_amount'] else 0
            order['apply_time'] = format_datetime(order['apply_time'])
            order['approve_time'] = format_datetime(order['approve_time'])
        
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
            'message': f'获取采购订单列表失败: {str(e)}'
        }), 500

@purchase_bp.route('/api/purchase-orders/<int:order_id>', methods=['GET'])
@login_required
def get_purchase_order(order_id):
    """获取采购订单详情"""
    try:
        conn = get_db_dict_connection()
        cursor = conn.cursor()
        
        # 获取订单基本信息
        cursor.execute("""
            SELECT po.id, po.order_no, po.supplier_id, s.name as supplier_name,
                   po.status, po.total_amount, po.apply_user_id, u1.real_name as apply_user_name,
                   po.approve_user_id, u2.real_name as approve_user_name,
                   po.apply_time, po.approve_time, po.remark
            FROM purchase_orders po
            LEFT JOIN suppliers s ON po.supplier_id = s.id
            LEFT JOIN users u1 ON po.apply_user_id = u1.id
            LEFT JOIN users u2 ON po.approve_user_id = u2.id
            WHERE po.id = %s
        """, (order_id,))
        
        order = cursor.fetchone()
        if not order:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '采购订单不存在'
            }), 404
        
        # 获取订单明细
        cursor.execute("""
            SELECT pd.id, pd.product_id, p.code, p.name as product_name, p.unit,
                   pd.quantity, pd.cost_price, pd.amount, pd.remark
            FROM purchase_details pd
            LEFT JOIN products p ON pd.product_id = p.id
            WHERE pd.purchase_id = %s
            ORDER BY pd.id
        """, (order_id,))
        
        details = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # 格式化数据
        order['total_amount'] = float(order['total_amount']) if order['total_amount'] else 0
        order['apply_time'] = format_datetime(order['apply_time'])
        order['approve_time'] = format_datetime(order['approve_time'])
        
        for detail in details:
            detail['cost_price'] = float(detail['cost_price'])
            detail['amount'] = float(detail['amount'])
        
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
            'message': f'获取采购订单详情失败: {str(e)}'
        }), 500

@purchase_bp.route('/api/purchase-orders', methods=['POST'])
@login_required
def create_purchase_order():
    """创建采购申请"""
    try:
        data = request.get_json() or {}
        
        # 验证必填字段
        required_fields = ['supplier_id', 'details']
        is_valid, message = validate_required_fields(data, required_fields)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': message
            })
        
        supplier_id = safe_int(data['supplier_id'])
        details = data['details']
        remark = safe_strip(data.get('remark'))
        
        if not details or len(details) == 0:
            return jsonify({
                'success': False,
                'message': '采购明细不能为空'
            })
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 验证供应商是否存在
            cursor.execute("SELECT id FROM suppliers WHERE id = %s AND status = 'active'", (supplier_id,))
            if not cursor.fetchone():
                return jsonify({
                    'success': False,
                    'message': '供应商不存在或已禁用'
                })
            
            # 验证商品并计算总金额
            total_amount = 0
            validated_details = []
            
            for detail in details:
                product_id = safe_int(detail.get('product_id'))
                quantity = safe_int(detail.get('quantity'))
                cost_price = safe_float(detail.get('cost_price'))
                detail_remark = safe_strip(detail.get('remark'))
                
                if not product_id or quantity <= 0 or cost_price <= 0:
                    return jsonify({
                        'success': False,
                        'message': '采购明细数据不完整或无效'
                    })
                
                # 验证商品是否存在
                cursor.execute("SELECT id FROM products WHERE id = %s AND status = 'active'", (product_id,))
                if not cursor.fetchone():
                    return jsonify({
                        'success': False,
                        'message': f'商品ID {product_id} 不存在或已禁用'
                    })
                
                amount = quantity * cost_price
                total_amount += amount
                
                validated_details.append({
                    'product_id': product_id,
                    'quantity': quantity,
                    'cost_price': cost_price,
                    'amount': amount,
                    'remark': detail_remark
                })
            
            # 生成订单号
            order_no = generate_order_no('PO')
            current_user = get_current_user()
            
            # 插入采购订单
            cursor.execute("""
                INSERT INTO purchase_orders (order_no, supplier_id, status, total_amount, 
                                           apply_user_id, apply_time, remark)
                VALUES (%s, %s, 'pending', %s, %s, %s, %s)
            """, (order_no, supplier_id, total_amount, current_user['user_id'], 
                  datetime.now(), remark or None))
            
            order_id = cursor.lastrowid
            
            # 插入采购明细
            for detail in validated_details:
                cursor.execute("""
                    INSERT INTO purchase_details (purchase_id, product_id, quantity, 
                                                cost_price, amount, remark)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (order_id, detail['product_id'], detail['quantity'],
                      detail['cost_price'], detail['amount'], detail['remark'] or None))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': '采购申请创建成功',
                'data': {
                    'order_id': order_id,
                    'order_no': order_no
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
            'message': f'创建采购申请失败: {str(e)}'
        }), 500

@purchase_bp.route('/api/purchase-orders/<int:order_id>/approve', methods=['PUT'])
@login_required
@manager_required
def approve_purchase_order(order_id):
    """审批采购申请"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查订单是否存在且状态为待审批
        cursor.execute("SELECT id, status FROM purchase_orders WHERE id = %s", (order_id,))
        order = cursor.fetchone()
        
        if not order:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '采购订单不存在'
            })
        
        if order[1] != 'pending':
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '只能审批状态为待审批的订单'
            })
        
        # 更新订单状态
        current_user = get_current_user()
        cursor.execute("""
            UPDATE purchase_orders 
            SET status = 'approved', approve_user_id = %s, approve_time = %s
            WHERE id = %s
        """, (current_user['user_id'], datetime.now(), order_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '采购申请审批通过'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'审批失败: {str(e)}'
        }), 500

@purchase_bp.route('/api/purchase-orders/<int:order_id>/reject', methods=['PUT'])
@login_required
@manager_required
def reject_purchase_order(order_id):
    """拒绝采购申请"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查订单是否存在且状态为待审批
        cursor.execute("SELECT id, status FROM purchase_orders WHERE id = %s", (order_id,))
        order = cursor.fetchone()
        
        if not order:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '采购订单不存在'
            })
        
        if order[1] != 'pending':
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '只能拒绝状态为待审批的订单'
            })
        
        # 更新订单状态
        current_user = get_current_user()
        cursor.execute("""
            UPDATE purchase_orders 
            SET status = 'cancelled', approve_user_id = %s, approve_time = %s
            WHERE id = %s
        """, (current_user['user_id'], datetime.now(), order_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '采购申请已拒绝'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'拒绝失败: {str(e)}'
        }), 500

@purchase_bp.route('/api/purchase-orders/<int:order_id>/deliver', methods=['PUT'])
@login_required
@manager_required
def deliver_purchase_order(order_id):
    """标记采购订单为已交付"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查订单是否存在且状态为已批准
        cursor.execute("SELECT id, status FROM purchase_orders WHERE id = %s", (order_id,))
        order = cursor.fetchone()
        
        if not order:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '采购订单不存在'
            })
        
        if order[1] != 'approved':
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '只能标记已批准的订单为已交付'
            })
        
        # 更新订单状态为已交付
        cursor.execute("""
            UPDATE purchase_orders 
            SET status = 'delivered'
            WHERE id = %s
        """, (order_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '采购订单已标记为已交付'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'更新状态失败: {str(e)}'
        }), 500

@purchase_bp.route('/api/purchase-orders/<int:order_id>', methods=['PUT'])
@login_required
def update_purchase_order(order_id):
    """更新采购申请（仅限待审批状态）"""
    try:
        data = request.get_json() or {}
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查订单是否存在且状态为待审批
        cursor.execute("SELECT id, status, apply_user_id FROM purchase_orders WHERE id = %s", (order_id,))
        order = cursor.fetchone()
        
        if not order:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '采购订单不存在'
            })
        
        if order[1] != 'pending':
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '只能修改状态为待审批的订单'
            })
        
        # 验证权限（只能修改自己的申请或管理员可以修改所有）
        current_user = get_current_user()
        if current_user['role'] != 'manager' and order[2] != current_user['user_id']:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '只能修改自己的采购申请'
            })
        
        try:
            # 构建更新字段
            update_fields = []
            params = []
            
            if 'supplier_id' in data:
                supplier_id = safe_int(data['supplier_id'])
                # 验证供应商
                cursor.execute("SELECT id FROM suppliers WHERE id = %s AND status = 'active'", (supplier_id,))
                if not cursor.fetchone():
                    return jsonify({
                        'success': False,
                        'message': '供应商不存在或已禁用'
                    })
                update_fields.append("supplier_id = %s")
                params.append(supplier_id)
            
            if 'remark' in data:
                update_fields.append("remark = %s")
                params.append(safe_strip(data['remark']) or None)
            
            # 处理明细更新
            if 'details' in data:
                details = data['details']
                if not details or len(details) == 0:
                    return jsonify({
                        'success': False,
                        'message': '采购明细不能为空'
                    })
                
                # 验证商品并计算总金额
                total_amount = 0
                validated_details = []
                
                for detail in details:
                    product_id = safe_int(detail.get('product_id'))
                    quantity = safe_int(detail.get('quantity'))
                    cost_price = safe_float(detail.get('cost_price'))
                    detail_remark = safe_strip(detail.get('remark'))
                    
                    if not product_id or quantity <= 0 or cost_price <= 0:
                        return jsonify({
                            'success': False,
                            'message': '采购明细数据不完整或无效'
                        })
                    
                    # 验证商品是否存在
                    cursor.execute("SELECT id FROM products WHERE id = %s AND status = 'active'", (product_id,))
                    if not cursor.fetchone():
                        return jsonify({
                            'success': False,
                            'message': f'商品ID {product_id} 不存在或已禁用'
                        })
                    
                    amount = quantity * cost_price
                    total_amount += amount
                    
                    validated_details.append({
                        'product_id': product_id,
                        'quantity': quantity,
                        'cost_price': cost_price,
                        'amount': amount,
                        'remark': detail_remark
                    })
                
                # 删除原有明细
                cursor.execute("DELETE FROM purchase_details WHERE purchase_id = %s", (order_id,))
                
                # 插入新明细
                for detail in validated_details:
                    cursor.execute("""
                        INSERT INTO purchase_details (purchase_id, product_id, quantity, 
                                                    cost_price, amount, remark)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (order_id, detail['product_id'], detail['quantity'],
                          detail['cost_price'], detail['amount'], detail['remark'] or None))
                
                # 更新总金额
                update_fields.append("total_amount = %s")
                params.append(total_amount)
            
            # 执行订单基本信息更新
            if update_fields:
                params.append(order_id)
                update_sql = f"UPDATE purchase_orders SET {', '.join(update_fields)} WHERE id = %s"
                cursor.execute(update_sql, params)
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': '采购申请更新成功'
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
            'message': f'更新采购申请失败: {str(e)}'
        }), 500

@purchase_bp.route('/api/purchase-orders/<int:order_id>', methods=['DELETE'])
@login_required
def delete_purchase_order(order_id):
    """删除采购申请（仅限待审批状态）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查订单是否存在且状态为待审批
        cursor.execute("SELECT id, status, apply_user_id FROM purchase_orders WHERE id = %s", (order_id,))
        order = cursor.fetchone()
        
        if not order:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '采购订单不存在'
            })
        
        if order[1] != 'pending':
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '只能删除状态为待审批的订单'
            })
        
        # 验证权限（只能删除自己的申请或管理员可以删除所有）
        current_user = get_current_user()
        if current_user['role'] != 'manager' and order[2] != current_user['user_id']:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '只能删除自己的采购申请'
            })
        
        try:
            # 删除采购明细
            cursor.execute("DELETE FROM purchase_details WHERE purchase_id = %s", (order_id,))
            
            # 删除采购订单
            cursor.execute("DELETE FROM purchase_orders WHERE id = %s", (order_id,))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': '采购申请删除成功'
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
            'message': f'删除采购申请失败: {str(e)}'
        }), 500

# ==================== 进货管理相关API ====================

@purchase_bp.route('/api/incoming-orders', methods=['GET'])
@login_required
def get_incoming_orders():
    """获取进货订单列表（分页）"""
    try:
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 10))
        search = safe_strip(request.args.get('search'))
        supplier_id = safe_strip(request.args.get('supplier_id'))
        start_date = safe_strip(request.args.get('start_date'))
        end_date = safe_strip(request.args.get('end_date'))
        
        conn = get_db_dict_connection()
        cursor = conn.cursor()
        
        # 构建查询条件
        where_conditions = []
        params = []
        
        if search:
            where_conditions.append("(io.order_no LIKE %s OR s.name LIKE %s OR u.real_name LIKE %s)")
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
        
        if supplier_id:
            where_conditions.append("io.supplier_id = %s")
            params.append(supplier_id)
        
        if start_date:
            where_conditions.append("io.incoming_date >= %s")
            params.append(start_date)
        
        if end_date:
            where_conditions.append("io.incoming_date <= %s")
            params.append(end_date)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # 计数查询
        count_query = f"""
            SELECT COUNT(*) 
            FROM incoming_orders io
            LEFT JOIN suppliers s ON io.supplier_id = s.id
            LEFT JOIN users u ON io.user_id = u.id
            {where_clause}
        """
        cursor.execute(count_query, params)
        total = cursor.fetchone()['COUNT(*)']
        
        # 数据查询
        offset = (page - 1) * size
        data_query = f"""
            SELECT io.id, io.order_no, io.purchase_id, po.order_no as purchase_order_no,
                   io.supplier_id, s.name as supplier_name, io.total_amount,
                   io.incoming_date, io.user_id, u.real_name as user_name,
                   io.created_at, io.remark
            FROM incoming_orders io
            LEFT JOIN suppliers s ON io.supplier_id = s.id
            LEFT JOIN users u ON io.user_id = u.id
            LEFT JOIN purchase_orders po ON io.purchase_id = po.id
            {where_clause}
            ORDER BY io.incoming_date DESC, io.created_at DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(data_query, params + [size, offset])
        orders = cursor.fetchall()
        
        # 格式化数据
        for order in orders:
            order['total_amount'] = float(order['total_amount']) if order['total_amount'] else 0
            order['incoming_date'] = format_date(order['incoming_date'])
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
            'message': f'获取进货订单列表失败: {str(e)}'
        }), 500

@purchase_bp.route('/api/incoming-orders/<int:order_id>', methods=['GET'])
@login_required
def get_incoming_order(order_id):
    """获取进货订单详情"""
    try:
        conn = get_db_dict_connection()
        cursor = conn.cursor()
        
        # 获取订单基本信息
        cursor.execute("""
            SELECT io.id, io.order_no, io.purchase_id, po.order_no as purchase_order_no,
                   io.supplier_id, s.name as supplier_name, io.total_amount,
                   io.incoming_date, io.user_id, u.real_name as user_name,
                   io.created_at, io.remark
            FROM incoming_orders io
            LEFT JOIN suppliers s ON io.supplier_id = s.id
            LEFT JOIN users u ON io.user_id = u.id
            LEFT JOIN purchase_orders po ON io.purchase_id = po.id
            WHERE io.id = %s
        """, (order_id,))
        
        order = cursor.fetchone()
        if not order:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '进货订单不存在'
            }), 404
        
        # 获取订单明细
        cursor.execute("""
            SELECT id.id, id.product_id, p.code, p.name as product_name, p.unit,
                   id.quantity, id.cost_price, id.amount, 
                   id.production_date, id.expiry_date, id.batch_no, id.remark
            FROM incoming_details id
            LEFT JOIN products p ON id.product_id = p.id
            WHERE id.incoming_id = %s
            ORDER BY id.id
        """, (order_id,))
        
        details = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # 格式化数据
        order['total_amount'] = float(order['total_amount']) if order['total_amount'] else 0
        order['incoming_date'] = format_date(order['incoming_date'])
        order['created_at'] = format_datetime(order['created_at'])
        
        for detail in details:
            detail['cost_price'] = float(detail['cost_price'])
            detail['amount'] = float(detail['amount'])
            detail['production_date'] = format_date(detail['production_date'])
            detail['expiry_date'] = format_date(detail['expiry_date'])
        
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
            'message': f'获取进货订单详情失败: {str(e)}'
        }), 500

@purchase_bp.route('/api/incoming-orders', methods=['POST'])
@login_required
def create_incoming_order():
    """创建进货订单"""
    try:
        data = request.get_json() or {}
        
        # 验证必填字段
        required_fields = ['supplier_id', 'incoming_date', 'details']
        is_valid, message = validate_required_fields(data, required_fields)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': message
            })
        
        supplier_id = safe_int(data['supplier_id'])
        incoming_date = data['incoming_date']
        purchase_id = safe_int(data.get('purchase_id', 0)) or None
        details = data['details']
        remark = safe_strip(data.get('remark'))
        
        if not details or len(details) == 0:
            return jsonify({
                'success': False,
                'message': '进货明细不能为空'
            })
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 验证供应商是否存在
            cursor.execute("SELECT id FROM suppliers WHERE id = %s AND status = 'active'", (supplier_id,))
            if not cursor.fetchone():
                return jsonify({
                    'success': False,
                    'message': '供应商不存在或已禁用'
                })
            
            # 如果指定了采购订单，验证采购订单（要求已交付 delivered）
            if purchase_id:
                cursor.execute("""
                    SELECT id, status FROM purchase_orders 
                    WHERE id = %s AND supplier_id = %s
                """, (purchase_id, supplier_id))
                po = cursor.fetchone()
                if not po:
                    return jsonify({
                        'success': False,
                        'message': '采购订单不存在或供应商不匹配'
                    })
                if po[1] != 'delivered':
                    return jsonify({
                        'success': False,
                        'message': '只能对已交付的采购订单进行进货'
                    })
            
            # 验证商品并计算总金额
            total_amount = 0
            validated_details = []
            
            for detail in details:
                product_id = safe_int(detail.get('product_id'))
                quantity = safe_int(detail.get('quantity'))
                cost_price = safe_float(detail.get('cost_price'))
                production_date = safe_strip(detail.get('production_date')) or None
                expiry_date = safe_strip(detail.get('expiry_date')) or None
                batch_no = safe_strip(detail.get('batch_no')) or None
                detail_remark = safe_strip(detail.get('remark'))
                
                if not product_id or quantity <= 0 or cost_price <= 0:
                    return jsonify({
                        'success': False,
                        'message': '进货明细数据不完整或无效'
                    })
                
                # 验证商品是否存在
                cursor.execute("SELECT id FROM products WHERE id = %s AND status = 'active'", (product_id,))
                if not cursor.fetchone():
                    return jsonify({
                        'success': False,
                        'message': f'商品ID {product_id} 不存在或已禁用'
                    })
                
                amount = quantity * cost_price
                total_amount += amount
                
                validated_details.append({
                    'product_id': product_id,
                    'quantity': quantity,
                    'cost_price': cost_price,
                    'amount': amount,
                    'production_date': production_date,
                    'expiry_date': expiry_date,
                    'batch_no': batch_no,
                    'remark': detail_remark
                })
            
            # 生成订单号
            order_no = generate_order_no('IN')
            current_user = get_current_user()
            
            # 插入进货订单
            cursor.execute("""
                INSERT INTO incoming_orders (order_no, purchase_id, supplier_id, total_amount, 
                                           incoming_date, user_id, remark)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (order_no, purchase_id, supplier_id, total_amount, 
                  incoming_date, current_user['user_id'], remark or None))
            
            order_id = cursor.lastrowid
            
            # 插入进货明细
            for detail in validated_details:
                cursor.execute("""
                    INSERT INTO incoming_details (incoming_id, product_id, quantity, 
                                                cost_price, amount, production_date, 
                                                expiry_date, batch_no, remark)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (order_id, detail['product_id'], detail['quantity'],
                      detail['cost_price'], detail['amount'], detail['production_date'],
                      detail['expiry_date'], detail['batch_no'], detail['remark'] or None))
                
                # 更新库存
                cursor.execute("""
                    UPDATE inventory 
                    SET quantity = quantity + %s, updated_at = NOW()
                    WHERE product_id = %s
                """, (detail['quantity'], detail['product_id']))
            
            # 如果关联了采购订单，更新采购订单状态为已入库（stock）
            if purchase_id:
                cursor.execute("""
                    UPDATE purchase_orders 
                    SET status = 'stock'
                    WHERE id = %s
                """, (purchase_id,))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': '进货订单创建成功',
                'data': {
                    'order_id': order_id,
                    'order_no': order_no
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
            'message': f'创建进货订单失败: {str(e)}'
        }), 500