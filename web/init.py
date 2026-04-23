import sqlite3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from settings import DS_CONFIG


DB_TYPE = DS_CONFIG['conn_type']
DB_CONFIG = None
SQLITE_DB_PATH = None

if DB_TYPE == 'sqlite':
    SQLITE_DB_PATH = DS_CONFIG['host']
elif DB_TYPE == 'mysql':
    DB_CONFIG = {
        'host': DS_CONFIG['host'],
        'port': int(DS_CONFIG['port']),
        'user': DS_CONFIG['username'],
        'password': DS_CONFIG['password'],
        'database': DS_CONFIG['db_name'],
        'charset': 'utf8mb4'
    }
elif DB_TYPE == 'mssql':
    DB_CONFIG = {
        'server': DS_CONFIG['host'],
        'port': int(DS_CONFIG['port']),
        'database': DS_CONFIG['db_name'],
        'driver': '{ODBC Driver 17 for SQL Server}',
        'trusted_connection': 'yes',
        'uid': DS_CONFIG['username'],
        'pwd': DS_CONFIG['password'],
    }
else:
    raise Exception('暂不支持的数据库')



# 尝试导入其他数据库驱动
try:
    import pymysql
    HAS_MYSQL = True
except ImportError:
    HAS_MYSQL = False

try:
    import pyodbc
    HAS_SQLSERVER = True
except ImportError:
    HAS_SQLSERVER = False


# ==================== 表定义 ====================
# 只读表
READONLY_TABLES = ['etl_log', 'etl_robot_message']

# 所有表的字段定义
TABLE_SCHEMAS = {
    'etl_log': {
        'id': 'bigint',
        'job_id': 'int',
        'message': 'longtext',
        'start_time': 'datetime',
        'job_params': 'longtext',
        'execution_status': 'int',
        'end_time': 'datetime'
    },
    'etl_robot_message': {
        'robot_id': 'int',
        'send_time': 'datetime',
        'text': 'longtext'
    },
    'etl_job_sync': {
        'id': 'int PRIMARY KEY',
        'from_server_id': 'int',
        'from_db_name': 'varchar(50)',
        'from_sql': 'longtext',
        'to_server_id': 'int',
        'to_db_name': 'varchar(50)',
        'to_table': 'varchar(100)',
        'to_columns': 'longtext',
        'param_server_id': 'int',
        'param_db_name': 'varchar(50)',
        'param_sql': 'varchar(255)',
        'before_write': 'longtext',
        'after_write': 'longtext',
        'last_execution_time': 'datetime',
        'note': 'varchar(255)'
    },
    'etl_job_sql': {
        'id': 'int PRIMARY KEY',
        'server_id': 'int',
        'db_name': 'varchar(50)',
        'sql_text': 'longtext',
        'remark': 'varchar(255)',
        'last_execution_time': 'datetime'
    },
    'etl_job_check': {
        'id': 'int PRIMARY KEY',
        'server_id': 'int',
        'db_name': 'varchar(50)',
        'check_sql': 'longtext',
        'robot_id': 'varchar(100)',
        'last_execution_time': 'datetime'
    },
    'etl_error_handling_config': {
        'id': 'int PRIMARY KEY',
        'error_pattern': 'varchar(255)',
        'pattern_desc': 'varchar(255)',
        'action_type': 'varchar(255)',
        'action_params': 'varchar(255)',
        'remark': 'varchar(255)'
    },
    'etl_robot': {
        'robot_id': 'int PRIMARY KEY',
        'name': 'varchar(50)',
        'access_token': 'varchar(100)',
        'secret': 'varchar(100)'
    },
    'etl_server': {
        'server_id': 'varchar(50) PRIMARY KEY',
        'server_name': 'varchar(100)',
        'host': 'varchar(200)',
        'port': 'varchar(10)',
        'username': 'varchar(100)',
        'password': 'varchar(150)',
        'db_name': 'varchar(50)',
        'conn_type': 'varchar(20)'
    }
}


# ==================== 数据库连接 ====================
def get_db_connection():
    """获取数据库连接"""
    if DB_TYPE == 'sqlite':
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    elif DB_TYPE == 'mysql':
        if not HAS_MYSQL:
            raise Exception("PyMySQL未安装，请运行: pip install pymysql")
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    elif DB_TYPE == 'mssql':
        if not HAS_SQLSERVER:
            raise Exception("pyodbc未安装，请运行: pip install pyodbc")
        # 构建服务器地址，包含端口号
        server_address = DB_CONFIG['server']
        if 'port' in DB_CONFIG and DB_CONFIG['port']:
            server_address += f",{DB_CONFIG['port']}"
        conn_str = f"DRIVER={DB_CONFIG['driver']};SERVER={server_address};DATABASE={DB_CONFIG['database']}"
        if DB_CONFIG['trusted_connection'] == 'yes':
            conn_str += ";Trusted_Connection=yes"
        else:
            conn_str += f";UID={DB_CONFIG['uid']};PWD={DB_CONFIG['pwd']}"
        conn = pyodbc.connect(conn_str)
        return conn
    else:
        raise Exception(f"不支持的数据库类型: {DB_TYPE}")


def init_database():
    """初始化数据库表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 根据数据库类型创建表
        for table_name, schema in TABLE_SCHEMAS.items():
            if DB_TYPE == 'sqlite':
                columns = ', '.join([f"{col} {dtype}" for col, dtype in schema.items()])
                create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns})"
            elif DB_TYPE == 'mysql':
                columns = ', '.join([f"`{col}` {dtype}" for col, dtype in schema.items()])
                create_sql = f"CREATE TABLE IF NOT EXISTS `{table_name}` ({columns}) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
            elif DB_TYPE == 'mssql':
                columns = ', '.join([f"[{col}] {dtype}" for col, dtype in schema.items()])
                create_sql = f"IF OBJECT_ID('{table_name}', 'U') IS NULL CREATE TABLE {table_name} ({columns})"
            
            cursor.execute(create_sql)
        
        conn.commit()
        print("数据库表初始化成功")
    except Exception as e:
        conn.rollback()
        print(f"数据库表初始化失败: {e}")
        raise
    finally:
        cursor.close()
        conn.close()






if __name__ == '__main__':
    init_database()
