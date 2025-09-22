"""
库存管理API模块
"""
from flask import Blueprint, request, jsonify
from utils.database import get_db_connection, get_db_dict_connection
from utils.auth import login_required, manager_required, get_current_user
from utils.helpers import validate_required_fields, generate_order_no, format_datetime, format_date, safe_int
from datetime import datetime

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/api/inventory', methods=['GET'])
@login_required
def get_inventory():
    """获取库存列表（分页）"""
    try:
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 10))
        search = request.args.get('search', '').strip()
        category = request.args.get('category', '').strip()
        low_stock = request.args.get('low_stock', '').lower() == 'true'
        zero_stock = request.args.get('zero_stock', '').lower() == 'true'
        
        conn = get_db_dict_connection()
        cursor = conn.cursor()
        
        # 构建查询条件
        where_conditions = ["p.status = 'active'"]
        params = []
        
        if search:
            where_conditions.append("(p.code LIKE %s OR p.name LIKE %s OR p.brand LIKE %s)")
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
        
        if category:
            where_conditions.append("p.category = %s")
            params.append(category)
        
        if zero_stock:
            where_conditions.append("COALESCE(i.quantity, 0) = 0")
        elif low_stock:
            where_conditions.append("COALESCE(i.quantity, 0) > 0 AND COALESCE(i.quantity, 0) <= 10")
        
        where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # 计数查询
        count_query = f"""
            SELECT COUNT(*) 
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            {where_clause}
        """
        cursor.execute(count_query, params)
        total = cursor.fetchone()['COUNT(*)']
        
        # 数据查询
        offset = (page - 1) * size
        data_query = f"""
            SELECT p.id, p.code, p.name, p.category, p.brand, p.unit, 
                   p.selling_price, COALESCE(i.quantity, 0) as quantity,
                   i.updated_at, i.remark as inventory_remark
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            {where_clause}
            ORDER BY p.name
            LIMIT %s OFFSET %s
        """
        cursor.execute(data_query, params + [size, offset])
        inventory = cursor.fetchall()
        
        # 格式化数据
        for item in inventory:
            item['selling_price'] = float(item['selling_price'])
            item['updated_at'] = format_datetime(item['updated_at'])
        
        cursor.close()
        conn.close()
        
        # 计算分页信息
        total_pages = (total + size - 1) // size
        
        return jsonify({
            'success': True,
            'data': inventory,
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
            'message': f'获取库存列表失败: {str(e)}'
        }), 500

@inventory_bp.route('/api/inventory/alerts', methods=['GET'])
@login_required
def get_inventory_alerts():
    """获取库存预警信息"""
    try:
        conn = get_db_dict_connection()
        cursor = conn.cursor()
        
        # 零库存商品
        cursor.execute("""
            SELECT p.id, p.code, p.name, p.category, p.brand, 
                   COALESCE(i.quantity, 0) as quantity
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            WHERE p.status = 'active' AND COALESCE(i.quantity, 0) = 0
            ORDER BY p.name
            LIMIT 50
        """)
        zero_stock = cursor.fetchall()
        
        # 低库存商品（1-10件）
        cursor.execute("""
            SELECT p.id, p.code, p.name, p.category, p.brand, 
                   COALESCE(i.quantity, 0) as quantity
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            WHERE p.status = 'active' 
              AND COALESCE(i.quantity, 0) > 0 
              AND COALESCE(i.quantity, 0) <= 10
            ORDER BY i.quantity, p.name
            LIMIT 50
        """)
        low_stock = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'zero_stock': zero_stock,
                'low_stock': low_stock,
                'zero_stock_count': len(zero_stock),
                'low_stock_count': len(low_stock)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取库存预警失败: {str(e)}'
        }), 500

@inventory_bp.route('/api/inventory/statistics', methods=['GET'])
@login_required
def get_inventory_statistics():
    """获取库存统计信息"""
    try:
        conn = get_db_dict_connection()
        cursor = conn.cursor()
        
        # 总体统计
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
        stats = cursor.fetchone()
        
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
        category_stats = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # 格式化数据
        stats['total_value'] = float(stats['total_value'])
        
        for cat in category_stats:
            cat['total_value'] = float(cat['total_value'])
        
        return jsonify({
            'success': True,
            'data': {
                'overview': stats,
                'by_category': category_stats
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取库存统计失败: {str(e)}'
        }), 500

# ==================== 库存盘点相关API ====================

@inventory_bp.route('/api/inventory-checks', methods=['GET'])
@login_required
def get_inventory_checks():
    """获取库存盘点列表（分页）"""
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
            where_conditions.append("(ic.check_no LIKE %s OR u.real_name LIKE %s)")
            params.extend([f'%{search}%', f'%{search}%'])
        
        if status:
            where_conditions.append("ic.status = %s")
            params.append(status)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # 计数查询
        count_query = f"""
            SELECT COUNT(*) 
            FROM inventory_checks ic
            LEFT JOIN users u ON ic.user_id = u.id
            {where_clause}
        """
        cursor.execute(count_query, params)
        total = cursor.fetchone()['COUNT(*)']
        
        # 数据查询
        offset = (page - 1) * size
        data_query = f"""
            SELECT ic.id, ic.check_no, ic.check_date, ic.status, 
                   ic.total_difference, ic.user_id, u.real_name as user_name,
                   ic.created_at, ic.remark
            FROM inventory_checks ic
            LEFT JOIN users u ON ic.user_id = u.id
            {where_clause}
            ORDER BY ic.check_date DESC, ic.created_at DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(data_query, params + [size, offset])
        checks = cursor.fetchall()
        
        # 格式化数据
        for check in checks:
            check['check_date'] = format_date(check['check_date'])
            check['created_at'] = format_datetime(check['created_at'])
        
        cursor.close()
        conn.close()
        
        # 计算分页信息
        total_pages = (total + size - 1) // size
        
        return jsonify({
            'success': True,
            'data': checks,
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
            'message': f'获取盘点列表失败: {str(e)}'
        }), 500

@inventory_bp.route('/api/inventory-checks/<int:check_id>', methods=['GET'])
@login_required
def get_inventory_check(check_id):
    """获取库存盘点详情"""
    try:
        conn = get_db_dict_connection()
        cursor = conn.cursor()
        
        # 获取盘点基本信息
        cursor.execute("""
            SELECT ic.id, ic.check_no, ic.check_date, ic.status, 
                   ic.total_difference, ic.user_id, u.real_name as user_name,
                   ic.created_at, ic.remark
            FROM inventory_checks ic
            LEFT JOIN users u ON ic.user_id = u.id
            WHERE ic.id = %s
        """, (check_id,))
        
        check = cursor.fetchone()
        if not check:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '库存盘点不存在'
            }), 404
        
        # 获取盘点明细
        cursor.execute("""
            SELECT icd.id, icd.product_id, p.code, p.name as product_name, p.unit,
                   icd.book_quantity, icd.actual_quantity, icd.difference,
                   icd.difference_type, icd.handled, icd.remark
            FROM inventory_check_details icd
            LEFT JOIN products p ON icd.product_id = p.id
            WHERE icd.check_id = %s
            ORDER BY icd.difference_type DESC, ABS(icd.difference) DESC
        """, (check_id,))
        
        details = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # 格式化数据
        check['check_date'] = format_date(check['check_date'])
        check['created_at'] = format_datetime(check['created_at'])
        
        for detail in details:
            detail['handled'] = bool(detail['handled'])
        
        return jsonify({
            'success': True,
            'data': {
                'check': check,
                'details': details
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取盘点详情失败: {str(e)}'
        }), 500

@inventory_bp.route('/api/inventory-checks', methods=['POST'])
@login_required
@manager_required
def create_inventory_check():
    """创建库存盘点"""
    try:
        data = request.get_json() or {}
        
        # 验证必填字段
        required_fields = ['check_date']
        is_valid, message = validate_required_fields(data, required_fields)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': message
            })
        
        check_date = data['check_date']
        remark = data.get('remark', '').strip()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 生成盘点单号
            check_no = generate_order_no('CHK')
            current_user = get_current_user()
            
            # 插入盘点单
            cursor.execute("""
                INSERT INTO inventory_checks (check_no, check_date, status, user_id, remark)
                VALUES (%s, %s, 'ongoing', %s, %s)
            """, (check_no, check_date, current_user['user_id'], remark or None))
            
            check_id = cursor.lastrowid
            
            # 获取所有商品当前库存并插入盘点明细
            cursor.execute("""
                SELECT p.id, COALESCE(i.quantity, 0) as current_quantity
                FROM products p
                LEFT JOIN inventory i ON p.id = i.product_id
                WHERE p.status = 'active'
                ORDER BY p.name
            """)
            
            products = cursor.fetchall()
            total_difference = 0
            
            for product in products:
                product_id, book_quantity = product
                actual_quantity = book_quantity  # 初始假设实际数量等于账面数量
                difference = actual_quantity - book_quantity
                
                if difference > 0:
                    difference_type = 'gain'
                elif difference < 0:
                    difference_type = 'loss'
                else:
                    difference_type = 'normal'
                
                total_difference += difference
                
                cursor.execute("""
                    INSERT INTO inventory_check_details 
                    (check_id, product_id, book_quantity, actual_quantity, 
                     difference, difference_type, handled)
                    VALUES (%s, %s, %s, %s, %s, %s, 0)
                """, (check_id, product_id, book_quantity, actual_quantity,
                      difference, difference_type))
            
            # 更新盘点单总差异
            cursor.execute("""
                UPDATE inventory_checks 
                SET total_difference = %s 
                WHERE id = %s
            """, (total_difference, check_id))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': '库存盘点创建成功',
                'data': {
                    'check_id': check_id,
                    'check_no': check_no,
                    'product_count': len(products)
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
            'message': f'创建库存盘点失败: {str(e)}'
        }), 500

@inventory_bp.route('/api/inventory-checks/<int:check_id>/update-quantity', methods=['PUT'])
@login_required
@manager_required
def update_check_quantity(check_id):
    """更新盘点数量"""
    try:
        data = request.get_json() or {}
        
        # 验证必填字段
        required_fields = ['product_id', 'actual_quantity']
        is_valid, message = validate_required_fields(data, required_fields)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': message
            })
        
        product_id = safe_int(data['product_id'])
        actual_quantity = safe_int(data['actual_quantity'])
        
        if actual_quantity < 0:
            return jsonify({
                'success': False,
                'message': '实际数量不能为负数'
            })
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 检查盘点单是否存在且状态为进行中
            cursor.execute("SELECT id, status FROM inventory_checks WHERE id = %s", (check_id,))
            check = cursor.fetchone()
            
            if not check:
                return jsonify({
                    'success': False,
                    'message': '库存盘点不存在'
                })
            
            if check[1] != 'ongoing':
                return jsonify({
                    'success': False,
                    'message': '只能修改进行中的盘点'
                })
            
            # 获取盘点明细
            cursor.execute("""
                SELECT id, book_quantity FROM inventory_check_details 
                WHERE check_id = %s AND product_id = %s
            """, (check_id, product_id))
            
            detail = cursor.fetchone()
            if not detail:
                return jsonify({
                    'success': False,
                    'message': '盘点明细不存在'
                })
            
            detail_id, book_quantity = detail
            difference = actual_quantity - book_quantity
            
            if difference > 0:
                difference_type = 'gain'
            elif difference < 0:
                difference_type = 'loss'
            else:
                difference_type = 'normal'
            
            # 更新盘点明细
            cursor.execute("""
                UPDATE inventory_check_details 
                SET actual_quantity = %s, difference = %s, difference_type = %s
                WHERE id = %s
            """, (actual_quantity, difference, difference_type, detail_id))
            
            # 重新计算总差异
            cursor.execute("""
                SELECT SUM(difference) FROM inventory_check_details 
                WHERE check_id = %s
            """, (check_id,))
            total_difference = cursor.fetchone()[0] or 0
            
            cursor.execute("""
                UPDATE inventory_checks 
                SET total_difference = %s 
                WHERE id = %s
            """, (total_difference, check_id))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': '盘点数量更新成功',
                'data': {
                    'difference': difference,
                    'difference_type': difference_type
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
            'message': f'更新盘点数量失败: {str(e)}'
        }), 500

@inventory_bp.route('/api/inventory-checks/<int:check_id>/complete', methods=['PUT'])
@login_required
@manager_required
def complete_inventory_check(check_id):
    """完成库存盘点并调整库存"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 检查盘点单是否存在且状态为进行中
            cursor.execute("SELECT id, status FROM inventory_checks WHERE id = %s", (check_id,))
            check = cursor.fetchone()
            
            if not check:
                return jsonify({
                    'success': False,
                    'message': '库存盘点不存在'
                })
            
            if check[1] != 'ongoing':
                return jsonify({
                    'success': False,
                    'message': '只能完成进行中的盘点'
                })
            
            # 获取所有盘点明细
            cursor.execute("""
                SELECT product_id, book_quantity, actual_quantity, difference, difference_type
                FROM inventory_check_details 
                WHERE check_id = %s AND difference != 0
            """, (check_id,))
            
            differences = cursor.fetchall()
            
            # 调整库存
            adjusted_count = 0
            for diff in differences:
                product_id, book_quantity, actual_quantity, difference, difference_type = diff
                # 盘盈盘亏直接加减库存数量（在当前库存基础上增减差异值）
                cursor.execute(
                    """
                    UPDATE inventory 
                    SET quantity = quantity + %s, updated_at = NOW()
                    WHERE product_id = %s
                    """,
                    (difference, product_id)
                )
                
                adjusted_count += 1
            
            # 标记所有明细为已处理
            cursor.execute("""
                UPDATE inventory_check_details 
                SET handled = 1 
                WHERE check_id = %s
            """, (check_id,))
            
            # 更新盘点单状态为已完成
            cursor.execute("""
                UPDATE inventory_checks 
                SET status = 'completed' 
                WHERE id = %s
            """, (check_id,))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': f'库存盘点完成，共调整 {adjusted_count} 个商品的库存'
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
            'message': f'完成库存盘点失败: {str(e)}'
        }), 500