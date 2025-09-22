"""
商品管理API模块
"""
from flask import Blueprint, request, jsonify
from utils.database import get_db_connection, get_db_dict_connection
from utils.auth import login_required, manager_required
from utils.helpers import validate_required_fields, format_datetime, safe_float

products_bp = Blueprint('products', __name__)

@products_bp.route('/api/products', methods=['GET'])
@login_required
def get_products():
    """获取商品列表（分页）"""
    try:
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 10))
        search = request.args.get('search', '').strip()
        category = request.args.get('category', '').strip()
        status = request.args.get('status', '').strip()
        
        conn = get_db_dict_connection()
        cursor = conn.cursor()
        
        # 构建查询条件
        where_conditions = []
        params = []
        
        if search:
            where_conditions.append("(p.code LIKE %s OR p.name LIKE %s OR p.brand LIKE %s)")
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
        
        if category:
            where_conditions.append("p.category = %s")
            params.append(category)
        
        if status:
            where_conditions.append("p.status = %s")
            params.append(status)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # 计数查询
        count_query = f"SELECT COUNT(*) FROM products p {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['COUNT(*)']
        
        # 数据查询（包含库存信息）
        offset = (page - 1) * size
        data_query = f"""
            SELECT p.id, p.code, p.name, p.category, p.brand, p.unit, 
                   p.selling_price, p.status, p.created_at, p.remark,
                   COALESCE(i.quantity, 0) as stock_quantity
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            {where_clause}
            ORDER BY p.created_at DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(data_query, params + [size, offset])
        products = cursor.fetchall()
        
        # 格式化数据
        for product in products:
            product['created_at'] = format_datetime(product['created_at'])
            product['selling_price'] = float(product['selling_price'])
        
        cursor.close()
        conn.close()
        
        # 计算分页信息
        total_pages = (total + size - 1) // size
        
        return jsonify({
            'success': True,
            'data': products,
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
            'message': f'获取商品列表失败: {str(e)}'
        }), 500

@products_bp.route('/api/products/<int:product_id>', methods=['GET'])
@login_required
def get_product(product_id):
    """获取商品详情"""
    try:
        conn = get_db_dict_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.id, p.code, p.name, p.category, p.brand, p.unit, 
                   p.selling_price, p.status, p.created_at, p.remark,
                   COALESCE(i.quantity, 0) as stock_quantity
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            WHERE p.id = %s
        """, (product_id,))
        
        product = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not product:
            return jsonify({
                'success': False,
                'message': '商品不存在'
            }), 404
        
        # 格式化数据
        product['created_at'] = format_datetime(product['created_at'])
        product['selling_price'] = float(product['selling_price'])
        
        return jsonify({
            'success': True,
            'data': product
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取商品详情失败: {str(e)}'
        }), 500

@products_bp.route('/api/products', methods=['POST'])
@login_required
@manager_required
def create_product():
    """创建商品"""
    try:
        data = request.get_json() or {}
        
        # 验证必填字段
        required_fields = ['name', 'selling_price']
        is_valid, message = validate_required_fields(data, required_fields)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': message
            })
        
        code = data.get('code', '').strip()
        name = data['name'].strip()
        category = data.get('category', '').strip()
        brand = data.get('brand', '').strip()
        unit = data.get('unit', '件').strip()
        selling_price = safe_float(data['selling_price'])
        remark = data.get('remark', '').strip()
        
        if selling_price <= 0:
            return jsonify({
                'success': False,
                'message': '销售价格必须大于0'
            })
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查商品编码是否重复
        if code:
            cursor.execute("SELECT id FROM products WHERE code = %s", (code,))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return jsonify({
                    'success': False,
                    'message': '商品编码已存在'
                })
        
        # 插入商品
        cursor.execute("""
            INSERT INTO products (code, name, category, brand, unit, selling_price, remark)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (code or None, name, category or None, brand or None, unit, selling_price, remark or None))
        
        product_id = cursor.lastrowid
        
        # 初始化库存
        cursor.execute("""
            INSERT INTO inventory (product_id, quantity, remark)
            VALUES (%s, 0, '初始库存')
        """, (product_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '商品创建成功',
            'data': {'product_id': product_id}
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'创建商品失败: {str(e)}'
        }), 500

@products_bp.route('/api/products/<int:product_id>', methods=['PUT'])
@login_required
@manager_required
def update_product(product_id):
    """更新商品信息"""
    try:
        data = request.get_json() or {}
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查商品是否存在
        cursor.execute("SELECT id FROM products WHERE id = %s", (product_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '商品不存在'
            })
        
        # 构建更新字段
        update_fields = []
        params = []
        
        if 'code' in data:
            code = data['code'].strip()
            if code:
                # 检查编码重复
                cursor.execute("SELECT id FROM products WHERE code = %s AND id != %s", (code, product_id))
                if cursor.fetchone():
                    cursor.close()
                    conn.close()
                    return jsonify({
                        'success': False,
                        'message': '商品编码已存在'
                    })
            update_fields.append("code = %s")
            params.append(code or None)
        
        if 'name' in data:
            update_fields.append("name = %s")
            params.append(data['name'].strip())
        
        if 'category' in data:
            update_fields.append("category = %s")
            params.append(data['category'].strip() or None)
        
        if 'brand' in data:
            update_fields.append("brand = %s")
            params.append(data['brand'].strip() or None)
        
        if 'unit' in data:
            update_fields.append("unit = %s")
            params.append(data['unit'].strip() or '件')
        
        if 'selling_price' in data:
            selling_price = safe_float(data['selling_price'])
            if selling_price <= 0:
                cursor.close()
                conn.close()
                return jsonify({
                    'success': False,
                    'message': '销售价格必须大于0'
                })
            update_fields.append("selling_price = %s")
            params.append(selling_price)
        
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
        params.append(product_id)
        update_sql = f"UPDATE products SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(update_sql, params)
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '商品信息更新成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'更新商品失败: {str(e)}'
        }), 500

@products_bp.route('/api/products/<int:product_id>', methods=['DELETE'])
@login_required
@manager_required
def delete_product(product_id):
    """删除商品"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查商品是否存在
        cursor.execute("SELECT id FROM products WHERE id = %s", (product_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '商品不存在'
            })
        
        # 检查是否有相关的业务数据
        cursor.execute("SELECT id FROM purchase_details WHERE product_id = %s LIMIT 1", (product_id,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '商品已有采购记录，不能删除'
            })
        
        cursor.execute("SELECT id FROM incoming_details WHERE product_id = %s LIMIT 1", (product_id,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '商品已有进货记录，不能删除'
            })
        
        cursor.execute("SELECT id FROM outgoing_details WHERE product_id = %s LIMIT 1", (product_id,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': '商品已有销售记录，不能删除'
            })
        
        # 删除库存记录
        cursor.execute("DELETE FROM inventory WHERE product_id = %s", (product_id,))
        
        # 删除商品
        cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '商品删除成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除商品失败: {str(e)}'
        }), 500

@products_bp.route('/api/products/categories', methods=['GET'])
@login_required
def get_categories():
    """获取商品分类列表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT category 
            FROM products 
            WHERE category IS NOT NULL AND category != ''
            ORDER BY category
        """)
        
        categories = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': categories
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取分类列表失败: {str(e)}'
        }), 500

@products_bp.route('/api/products/brands', methods=['GET'])
@login_required
def get_brands():
    """获取品牌列表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT brand 
            FROM products 
            WHERE brand IS NOT NULL AND brand != ''
            ORDER BY brand
        """)
        
        brands = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': brands
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取品牌列表失败: {str(e)}'
        }), 500

@products_bp.route('/api/products/search', methods=['GET'])
@login_required
def search_products():
    """搜索商品（用于选择器）"""
    try:
        keyword = request.args.get('keyword', '').strip()
        limit = int(request.args.get('limit', 20))
        
        conn = get_db_dict_connection()
        cursor = conn.cursor()
        
        where_clause = "WHERE p.status = 'active'"
        params = []
        
        if keyword:
            where_clause += " AND (p.code LIKE %s OR p.name LIKE %s OR p.brand LIKE %s)"
            params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])
        
        cursor.execute(f"""
            SELECT p.id, p.code, p.name, p.category, p.brand, p.unit, 
                   p.selling_price, COALESCE(i.quantity, 0) as stock_quantity
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            {where_clause}
            ORDER BY p.name
            LIMIT %s
        """, params + [limit])
        
        products = cursor.fetchall()
        
        # 格式化数据
        for product in products:
            product['selling_price'] = float(product['selling_price'])
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': products
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'搜索商品失败: {str(e)}'
        }), 500