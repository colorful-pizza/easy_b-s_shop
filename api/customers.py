"""
客户管理API模块
"""
from flask import Blueprint, request, jsonify
from utils.database import get_db_connection, get_db_dict_connection
from utils.auth import login_required, manager_required
from utils.helpers import validate_required_fields, validate_phone, format_datetime

customers_bp = Blueprint('customers', __name__)

@customers_bp.route('/api/customers', methods=['GET'])
@login_required
def get_customers():
    """获取客户列表（分页）"""
    try:
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 10))
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '').strip()
        include_default = request.args.get('include_default', 'true').lower() == 'true'
        
        conn = get_db_dict_connection()
        cursor = conn.cursor()
        
        # 构建查询条件
        where_conditions = []
        params = []
        
        if not include_default:
            where_conditions.append("is_default = 0")
        
        if search:
            where_conditions.append("(name LIKE %s OR phone LIKE %s)")
            params.extend([f'%{search}%', f'%{search}%'])
        
        if status:
            where_conditions.append("status = %s")
            params.append(status)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # 计数查询
        count_query = f"SELECT COUNT(*) FROM customers {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['COUNT(*)']
        
        # 数据查询
        offset = (page - 1) * size
        data_query = f"""
            SELECT id, name, phone, address, is_default, status, created_at, remark
            FROM customers 
            {where_clause}
            ORDER BY is_default DESC, created_at DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(data_query, params + [size, offset])
        customers = cursor.fetchall()
        
        # 格式化数据
        for customer in customers:
            customer['created_at'] = format_datetime(customer['created_at'])
            customer['is_default'] = bool(customer['is_default'])
        
        cursor.close()
        conn.close()
        
        # 计算分页信息
        total_pages = (total + size - 1) // size
        
        return jsonify({
            'success': True,
            'data': customers,
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
            'message': f'获取客户列表失败: {str(e)}'
        }), 500

@customers_bp.route('/api/customers/<int:customer_id>', methods=['GET'])
@login_required
def get_customer(customer_id):
    """获取客户详情"""
    try:
        conn = get_db_dict_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, phone, address, is_default, status, created_at, remark
            FROM customers
            WHERE id = %s
        """, (customer_id,))
        
        customer = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not customer:
            return jsonify({
                'success': False,
                'message': '客户不存在'
            }), 404
        
        # 格式化数据
        customer['created_at'] = format_datetime(customer['created_at'])
        customer['is_default'] = bool(customer['is_default'])
        
        return jsonify({
            'success': True,
            'data': customer
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取客户详情失败: {str(e)}'
        }), 500

@customers_bp.route('/api/customers', methods=['POST'])
@login_required
def create_customer():
    """创建客户"""
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
        
        # 插入客户
        cursor.execute("""
            INSERT INTO customers (name, phone, address, is_default, remark)
            VALUES (%s, %s, %s, 0, %s)
        """, (name, phone or None, address or None, remark or None))
        
        customer_id = cursor.lastrowid
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '客户创建成功',
            'data': {'customer_id': customer_id}
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'创建客户失败: {str(e)}'
        }), 500

@customers_bp.route('/api/customers/<int:customer_id>', methods=['PUT'])
@login_required
def update_customer(customer_id):
    """更新客户信息"""
    try:
        data = request.get_json() or {}
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查客户是否存在
        cursor.execute("SELECT id, is_default FROM customers WHERE id = %s", (customer_id,))
        customer = cursor.fetchone()
        if not customer:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '客户不存在'
            })
        
        # 不允许修改默认客户（散户）
        if customer[1] == 1:  # is_default
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '不能修改默认客户（散户）'
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
                    'message': '客户名称不能为空'
                })
            update_fields.append("name = %s")
            params.append(name)
        
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
        params.append(customer_id)
        update_sql = f"UPDATE customers SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(update_sql, params)
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '客户信息更新成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'更新客户失败: {str(e)}'
        }), 500

@customers_bp.route('/api/customers/<int:customer_id>', methods=['DELETE'])
@login_required
@manager_required
def delete_customer(customer_id):
    """删除客户"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查客户是否存在
        cursor.execute("SELECT id, is_default FROM customers WHERE id = %s", (customer_id,))
        customer = cursor.fetchone()
        if not customer:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '客户不存在'
            })
        
        # 不能删除默认客户（散户）
        if customer[1] == 1:  # is_default
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '不能删除默认客户（散户）'
            })
        
        # 检查是否有相关的业务数据
        cursor.execute("SELECT id FROM outgoing_orders WHERE customer_id = %s LIMIT 1", (customer_id,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '客户已有销售记录，不能删除'
            })
        
        # 删除客户
        cursor.execute("DELETE FROM customers WHERE id = %s", (customer_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '客户删除成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除客户失败: {str(e)}'
        }), 500

@customers_bp.route('/api/customers/search', methods=['GET'])
@login_required
def search_customers():
    """搜索客户（用于选择器）"""
    try:
        keyword = request.args.get('keyword', '').strip()
        limit = int(request.args.get('limit', 20))
        include_default = request.args.get('include_default', 'true').lower() == 'true'
        
        conn = get_db_dict_connection()
        cursor = conn.cursor()
        
        where_conditions = ["status = 'active'"]
        params = []
        
        if not include_default:
            where_conditions.append("is_default = 0")
        
        if keyword:
            where_conditions.append("(name LIKE %s OR phone LIKE %s)")
            params.extend([f'%{keyword}%', f'%{keyword}%'])
        
        where_clause = "WHERE " + " AND ".join(where_conditions)
        
        cursor.execute(f"""
            SELECT id, name, phone, address, is_default
            FROM customers
            {where_clause}
            ORDER BY is_default DESC, name
            LIMIT %s
        """, params + [limit])
        
        customers = cursor.fetchall()
        
        # 格式化数据
        for customer in customers:
            customer['is_default'] = bool(customer['is_default'])
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': customers
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'搜索客户失败: {str(e)}'
        }), 500

@customers_bp.route('/api/customers/default', methods=['GET'])
@login_required
def get_default_customer():
    """获取默认客户（散户）"""
    try:
        conn = get_db_dict_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, phone, address, is_default, status, created_at, remark
            FROM customers
            WHERE is_default = 1
            LIMIT 1
        """)
        
        customer = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not customer:
            return jsonify({
                'success': False,
                'message': '未找到默认客户'
            }), 404
        
        # 格式化数据
        customer['created_at'] = format_datetime(customer['created_at'])
        customer['is_default'] = bool(customer['is_default'])
        
        return jsonify({
            'success': True,
            'data': customer
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取默认客户失败: {str(e)}'
        }), 500