"""
创建测试用户
"""
import pymysql
from utils.auth import hash_password

def create_test_users():
    """创建测试用户"""
    try:
        # 连接数据库
        connection = pymysql.connect(
            host='localhost',
            port=3306,
            user='root',
            password='123456',
            database='shop',
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # 删除现有测试用户
        cursor.execute("DELETE FROM users WHERE username IN ('admin', 'staff')")
        
        # 创建管理员用户
        admin_password = hash_password('123456')
        cursor.execute("""
            INSERT INTO users (username, password, role, status, created_at) 
            VALUES (%s, %s, %s, %s, NOW())
        """, ('admin', admin_password, 'manager', 'active'))
        
        # 创建店员用户
        staff_password = hash_password('123456')
        cursor.execute("""
            INSERT INTO users (username, password, role, status, created_at) 
            VALUES (%s, %s, %s, %s, NOW())
        """, ('staff', staff_password, 'staff', 'active'))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("测试用户创建成功！")
        print("管理员账户：admin / 123456")
        print("店员账户：staff / 123456")
        
    except Exception as e:
        print(f"创建测试用户失败: {str(e)}")

if __name__ == '__main__':
    create_test_users()