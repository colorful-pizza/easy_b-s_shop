"""
数据库连接和配置模块
"""
import pymysql

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'database': 'shop',
    'charset': 'utf8mb4'
}

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)

def get_db_dict_connection():
    """获取字典游标的数据库连接"""
    config = DB_CONFIG.copy()
    config['cursorclass'] = pymysql.cursors.DictCursor
    return pymysql.connect(**config)