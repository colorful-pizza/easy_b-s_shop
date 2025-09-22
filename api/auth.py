"""
用户认证API模块
"""
from flask import Blueprint, request, jsonify, session
from utils.database import get_db_connection, get_db_dict_connection
from utils.auth import hash_password, login_required, manager_required, get_current_user, paginate_query
from utils.helpers import validate_required_fields, validate_phone, format_datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({
                'success': False,
                'message': '用户名和密码不能为空'
            })
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 查询用户
        cursor.execute("""
            SELECT id, username, password, real_name, role, status 
            FROM users 
            WHERE username = %s
        """, (username,))
        
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户名或密码错误'
            })
        
        user_id, db_username, db_password, real_name, role, status = user
        
        if status == 'inactive':
            return jsonify({
                'success': False,
                'message': '账户已被禁用'
            })
        
        # 验证密码
        if hash_password(password) != db_password:
            return jsonify({
                'success': False,
                'message': '用户名或密码错误'
            })
        
        # 设置会话
        session['user_id'] = user_id
        session['username'] = db_username
        session['real_name'] = real_name
        session['role'] = role
        
        return jsonify({
            'success': True,
            'message': '登录成功',
            'data': {
                'user_id': user_id,
                'username': db_username,
                'real_name': real_name,
                'role': role
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'登录失败: {str(e)}'
        }), 500

@auth_bp.route('/api/auth/logout', methods=['POST'])
@login_required
def logout():
    """用户登出"""
    session.clear()
    return jsonify({
        'success': True,
        'message': '已退出登录'
    })

@auth_bp.route('/api/auth/current-user', methods=['GET'])
@login_required
def current_user():
    """获取当前用户信息"""
    user = get_current_user()
    return jsonify({
        'success': True,
        'data': user
    })

@auth_bp.route('/api/users', methods=['GET'])
@login_required
@manager_required
def get_users():
    """获取用户列表（分页）"""
    try:
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 10))
        search = request.args.get('search', '').strip()
        role_filter = request.args.get('role', '').strip()
        status_filter = request.args.get('status', '').strip()
        
        conn = get_db_dict_connection()
        cursor = conn.cursor()
        
        # 构建查询条件
        where_conditions = []
        params = []
        
        if search:
            where_conditions.append("(username LIKE %s OR real_name LIKE %s)")
            params.extend([f'%{search}%', f'%{search}%'])
        
        if role_filter:
            where_conditions.append("role = %s")
            params.append(role_filter)
        
        if status_filter:
            where_conditions.append("status = %s")
            params.append(status_filter)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # 计数查询
        count_query = f"SELECT COUNT(*) FROM users {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['COUNT(*)']
        
        # 数据查询
        offset = (page - 1) * size
        data_query = f"""
            SELECT id, username, real_name, role, phone, status, created_at, remark
            FROM users 
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(data_query, params + [size, offset])
        users = cursor.fetchall()
        
        # 格式化数据
        for user in users:
            user['created_at'] = format_datetime(user['created_at'])
        
        cursor.close()
        conn.close()
        
        # 计算分页信息
        total_pages = (total + size - 1) // size
        
        return jsonify({
            'success': True,
            'data': users,
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
            'message': f'获取用户列表失败: {str(e)}'
        }), 500

@auth_bp.route('/api/users', methods=['POST'])
@login_required
@manager_required
def create_user():
    """创建用户"""
    try:
        data = request.get_json() or {}
        
        # 验证必填字段
        required_fields = ['username', 'password', 'real_name', 'role']
        is_valid, message = validate_required_fields(data, required_fields)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': message
            })
        
        username = data['username'].strip()
        password = data['password'].strip()
        real_name = data['real_name'].strip()
        role = data['role'].strip()
        phone = data.get('phone', '').strip()
        remark = data.get('remark', '').strip()
        
        # 验证角色
        if role not in ['manager', 'staff']:
            return jsonify({
                'success': False,
                'message': '角色只能是manager或staff'
            })
        
        # 验证手机号
        if phone and not validate_phone(phone):
            return jsonify({
                'success': False,
                'message': '手机号格式不正确'
            })
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查用户名是否已存在
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '用户名已存在'
            })
        
        # 插入用户
        cursor.execute("""
            INSERT INTO users (username, password, real_name, role, phone, remark)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (username, hash_password(password), real_name, role, phone or None, remark or None))
        
        conn.commit()
        user_id = cursor.lastrowid
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '用户创建成功',
            'data': {'user_id': user_id}
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'创建用户失败: {str(e)}'
        }), 500

@auth_bp.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
@manager_required
def update_user(user_id):
    """更新用户信息"""
    try:
        data = request.get_json() or {}
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查用户是否存在
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '用户不存在'
            })
        
        # 构建更新字段
        update_fields = []
        params = []
        
        if 'real_name' in data:
            update_fields.append("real_name = %s")
            params.append(data['real_name'].strip())
        
        if 'role' in data:
            role = data['role'].strip()
            if role not in ['manager', 'staff']:
                cursor.close()
                conn.close()
                return jsonify({
                    'success': False,
                    'message': '角色只能是manager或staff'
                })
            update_fields.append("role = %s")
            params.append(role)
        
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
        
        if 'password' in data and data['password'].strip():
            update_fields.append("password = %s")
            params.append(hash_password(data['password'].strip()))
        
        if not update_fields:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '没有需要更新的字段'
            })
        
        # 执行更新
        params.append(user_id)
        update_sql = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(update_sql, params)
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '用户信息更新成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'更新用户失败: {str(e)}'
        }), 500

@auth_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
@manager_required
def delete_user(user_id):
    """删除用户"""
    try:
        current_user = get_current_user()
        
        # 不能删除自己
        if current_user['user_id'] == user_id:
            return jsonify({
                'success': False,
                'message': '不能删除自己的账户'
            })
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查用户是否存在
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '用户不存在'
            })
        
        # 删除用户
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '用户删除成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除用户失败: {str(e)}'
        }), 500

@auth_bp.route('/api/auth/change-password', methods=['POST'])
@login_required
def change_password():
    """修改密码"""
    try:
        data = request.get_json() or {}
        old_password = data.get('old_password', '').strip()
        new_password = data.get('new_password', '').strip()
        
        if not old_password or not new_password:
            return jsonify({
                'success': False,
                'message': '旧密码和新密码不能为空'
            })
        
        current_user = get_current_user()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 验证旧密码
        cursor.execute("SELECT password FROM users WHERE id = %s", (current_user['user_id'],))
        db_password = cursor.fetchone()[0]
        
        if hash_password(old_password) != db_password:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '旧密码不正确'
            })
        
        # 更新密码
        cursor.execute(
            "UPDATE users SET password = %s WHERE id = %s",
            (hash_password(new_password), current_user['user_id'])
        )
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '密码修改成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'修改密码失败: {str(e)}'
        }), 500