"""
认证和权限管理模块
"""
from functools import wraps
from flask import session, jsonify, request
import hashlib

def hash_password(password):
    """密码加密"""
    return hashlib.md5(password.encode()).hexdigest()

def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'message': '请先登录',
                'code': 401
            }), 401
        return f(*args, **kwargs)
    return decorated_function

def manager_required(f):
    """管理员权限验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'message': '请先登录',
                'code': 401
            }), 401
        
        if session.get('role') != 'manager':
            return jsonify({
                'success': False,
                'message': '权限不足，需要管理员权限',
                'code': 403
            }), 403
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """获取当前登录用户信息"""
    if 'user_id' in session:
        return {
            'user_id': session['user_id'],
            'username': session['username'],
            'role': session['role'],
            'real_name': session.get('real_name')
        }
    return None

def paginate_query(cursor, page=1, size=10, count_query=None, data_query=None):
    """
    分页查询辅助函数
    
    Args:
        cursor: 数据库游标
        page: 页码（从1开始）
        size: 每页数量
        count_query: 计数查询SQL
        data_query: 数据查询SQL
    
    Returns:
        dict: 包含分页信息的结果
    """
    # 计算偏移量
    offset = (page - 1) * size
    
    # 执行计数查询
    cursor.execute(count_query)
    total = cursor.fetchone()[0]
    
    # 执行数据查询
    data_query_with_limit = f"{data_query} LIMIT {size} OFFSET {offset}"
    cursor.execute(data_query_with_limit)
    data = cursor.fetchall()
    
    # 计算总页数
    total_pages = (total + size - 1) // size
    
    return {
        'data': data,
        'pagination': {
            'page': page,
            'size': size,
            'total': total,
            'total_pages': total_pages,
            'has_prev': page > 1,
            'has_next': page < total_pages
        }
    }