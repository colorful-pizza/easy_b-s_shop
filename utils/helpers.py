"""
通用工具函数模块
"""
from datetime import datetime
import re

def generate_order_no(prefix=''):
    """生成订单号"""
    now = datetime.now()
    return f"{prefix}{now.strftime('%Y%m%d%H%M%S')}"

def validate_phone(phone):
    """验证手机号格式"""
    if not phone:
        return True  # 允许为空
    pattern = r'^1[3-9]\d{9}$'
    return re.match(pattern, phone) is not None

def validate_required_fields(data, required_fields):
    """验证必填字段"""
    missing_fields = []
    for field in required_fields:
        if field not in data or not str(data[field]).strip():
            missing_fields.append(field)
    
    if missing_fields:
        return False, f"缺少必填字段: {', '.join(missing_fields)}"
    return True, ""

def format_datetime(dt):
    """格式化日期时间"""
    if dt is None:
        return ""
    if isinstance(dt, datetime):
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    return str(dt)

def format_date(dt):
    """格式化日期"""
    if dt is None:
        return ""
    if isinstance(dt, datetime):
        return dt.strftime('%Y-%m-%d')
    return str(dt)

def safe_float(value, default=0.0):
    """安全转换为浮点数"""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    """安全转换为整数"""
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def safe_strip(value: object) -> str:
    """安全地对可能为None的值执行strip，返回空字符串而不是抛错"""
    return value.strip() if isinstance(value, str) else ""