"""
CheapETL-UI 数据管理后端服务
支持MySQL、SQL Server、SQLite数据库
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
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

app = Flask(__name__)
CORS(app)  # 允许跨域请求



# ==================== 表定义 ====================
# 只读表
READONLY_TABLES = ['etl_log', 'etl_robot_message']

# 表显示名称配置
TABLE_DISPLAY_NAMES = {
    'etl_log': 'ETL作业日志',
    'etl_robot_message': '机器人消息',
    'etl_job_sync': '数据同步作业',
    'etl_job_sql': 'SQL作业',
    'etl_job_check': '检查作业',
    'etl_error_handling_config': '错误处理配置',
    'etl_robot': '机器人配置',
    'etl_server': '服务器配置'
}

# 字段显示名称配置
FIELD_DISPLAY_NAMES = {
    'etl_log': {
        'id': 'ID',
        'job_id': '作业ID',
        'message': '消息',
        'start_time': '开始时间',
        'job_params': '作业参数',
        'execution_status': '执行状态',
        'end_time': '结束时间'
    },
    'etl_robot_message': {
        'robot_id': '机器人ID',
        'send_time': '发送时间',
        'text': '消息内容'
    },
    'etl_job_sync': {
        'id': 'ID',
        'from_server_id': '源服务器ID',
        'from_db_name': '源数据库',
        'from_sql': '源SQL',
        'to_server_id': '目标服务器ID',
        'to_db_name': '目标数据库',
        'to_table': '目标表',
        'to_columns': '目标字段',
        'param_server_id': '参数服务器ID',
        'param_db_name': '参数数据库',
        'param_sql': '参数SQL',
        'before_write': '写入前SQL',
        'after_write': '写入后SQL',
        'last_execution_time': '最后执行时间',
        'note': '备注'
    },
    'etl_job_sql': {
        'id': 'ID',
        'server_id': '服务器ID',
        'db_name': '数据库',
        'sql_text': 'SQL语句',
        'remark': '备注',
        'last_execution_time': '最后执行时间'
    },
    'etl_job_check': {
        'id': 'ID',
        'server_id': '服务器ID',
        'db_name': '数据库',
        'check_sql': '检查SQL',
        'robot_id': '机器人ID',
        'last_execution_time': '最后执行时间'
    },
    'etl_error_handling_config': {
        'id': 'ID',
        'error_pattern': '错误模式',
        'pattern_desc': '模式描述',
        'action_type': '动作类型',
        'action_params': '动作参数',
        'remark': '备注'
    },
    'etl_robot': {
        'robot_id': '群机器人ID',
        'name': '名称',
        'access_token': 'access_token',
        'secret': 'secret'
    },
    'etl_server': {
        'server_id': '服务器ID',
        'server_name': '服务器名称',
        'host': '主机',
        'port': '端口',
        'username': '用户名',
        'password': '密码',
        'db_name': '数据库',
        'conn_type': '连接类型(mysql,mssql,sqlite,oracle)'
    }
}

# 字段显示顺序配置
FIELD_DISPLAY_ORDER = {
    'etl_log': ['id', 'job_id', 'execution_status', 'start_time', 'end_time', 'job_params', 'message'],
    'etl_robot_message': ['robot_id', 'send_time', 'text'],
    'etl_job_sync': ['id', 'from_server_id', 'from_db_name', 'from_sql', 'to_server_id', 'to_db_name', 'to_table', 'to_columns', 'param_server_id', 'param_db_name', 'param_sql', 'before_write', 'after_write', 'last_execution_time', 'note'],
    'etl_job_sql': ['id', 'server_id', 'db_name', 'sql_text', 'remark', 'last_execution_time'],
    'etl_job_check': ['id', 'server_id', 'db_name', 'check_sql', 'robot_id', 'last_execution_time'],
    'etl_error_handling_config': ['id', 'error_pattern', 'pattern_desc', 'action_type', 'action_params', 'remark'],
    'etl_robot': ['robot_id', 'name', 'access_token', 'secret'],
    'etl_server': ['server_id', 'server_name', 'conn_type', 'host', 'port', 'username', 'password', 'db_name']
}

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


# ==================== 通用CRUD操作 ====================
def execute_query(sql, params=None):
    """执行查询语句"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        
        rows = cursor.fetchall()
        
        # 转换为字典列表
        if DB_TYPE == 'sqlite':
            result = [dict(row) for row in rows]
        else:
            columns = [desc[0] for desc in cursor.description]
            result = [dict(zip(columns, row)) for row in rows]
        
        return result
    finally:
        cursor.close()
        conn.close()


def execute_update(sql, params=None):
    """执行更新语句"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        
        conn.commit()
        return cursor.rowcount
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


# ==================== API路由 ====================
@app.route('/api/tables', methods=['GET'])
def get_tables():
    """获取所有表名"""
    # 构建包含显示名称的表列表
    tables = []
    for table_name in TABLE_SCHEMAS.keys():
        tables.append({
            'name': table_name,
            'display_name': TABLE_DISPLAY_NAMES.get(table_name, table_name)
        })
    
    return jsonify({
        'success': True,
        'data': tables,
        'readonly_tables': READONLY_TABLES
    })


@app.route('/api/schema/<table_name>', methods=['GET'])
def get_table_schema(table_name):
    """获取表结构"""
    if table_name not in TABLE_SCHEMAS:
        return jsonify({'success': False, 'error': f'表 {table_name} 不存在'})
    
    # 获取字段显示顺序，如果没有配置则使用默认顺序
    field_order = FIELD_DISPLAY_ORDER.get(table_name, list(TABLE_SCHEMAS[table_name].keys()))
    
    # 构建包含显示信息的字段列表
    fields = []
    for field_name in field_order:
        if field_name in TABLE_SCHEMAS[table_name]:
            field_info = {
                'name': field_name,
                'type': TABLE_SCHEMAS[table_name][field_name],
                'display_name': FIELD_DISPLAY_NAMES.get(table_name, {}).get(field_name, field_name)
            }
            fields.append(field_info)
    
    return jsonify({
        'success': True,
        'data': fields,
        'table_display_name': TABLE_DISPLAY_NAMES.get(table_name, table_name),
        'readonly': table_name in READONLY_TABLES
    })


@app.route('/api/data/<table_name>', methods=['GET'])
def get_table_data(table_name):
    """获取表数据（支持分页）"""
    if table_name not in TABLE_SCHEMAS:
        return jsonify({'success': False, 'error': f'表 {table_name} 不存在'})
    
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 50, type=int)
    
    # 限制page_size范围
    page_size = min(max(page_size, 1), 1000)
    
    offset = (page - 1) * page_size
    
    try:
        # 获取总记录数
        count_sql = f"SELECT COUNT(*) as total FROM {table_name}"
        count_result = execute_query(count_sql)
        total = count_result[0]['total'] if count_result else 0
        
        # 获取数据
        if DB_TYPE == 'mysql':
            data_sql = f"SELECT * FROM `{table_name}` LIMIT %s OFFSET %s"
            data = execute_query(data_sql, (page_size, offset))
        elif DB_TYPE == 'mssql':
            data_sql = f"SELECT * FROM [{table_name}] ORDER BY (SELECT NULL) OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
            data = execute_query(data_sql, (offset, page_size))
        else:  # sqlite
            data_sql = f"SELECT * FROM {table_name} LIMIT ? OFFSET ?"
            data = execute_query(data_sql, (page_size, offset))
        
        return jsonify({
            'success': True,
            'data': data,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/data/<table_name>/<record_id>', methods=['GET'])
def get_record(table_name, record_id):
    """获取单条记录"""
    if table_name not in TABLE_SCHEMAS:
        return jsonify({'success': False, 'error': f'表 {table_name} 不存在'})
    
    try:
        # 获取主键字段
        schema = TABLE_SCHEMAS[table_name]
        primary_key = None
        for col, dtype in schema.items():
            if 'PRIMARY KEY' in dtype:
                primary_key = col
                break
        
        if not primary_key:
            primary_key = 'id'  # 默认使用id字段
        
        if DB_TYPE == 'mysql':
            sql = f"SELECT * FROM `{table_name}` WHERE `{primary_key}` = %s"
        elif DB_TYPE == 'mssql':
            sql = f"SELECT * FROM [{table_name}] WHERE [{primary_key}] = ?"
        else:
            sql = f"SELECT * FROM {table_name} WHERE {primary_key} = ?"
        
        records = execute_query(sql, (record_id,))
        
        if not records:
            return jsonify({'success': False, 'error': '记录不存在'})
        
        return jsonify({'success': True, 'data': records[0]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/data/<table_name>', methods=['POST'])
def create_record(table_name):
    """创建新记录"""
    if table_name in READONLY_TABLES:
        return jsonify({'success': False, 'error': f'表 {table_name} 是只读的，不允许插入数据'})
    
    if table_name not in TABLE_SCHEMAS:
        return jsonify({'success': False, 'error': f'表 {table_name} 不存在'})
    
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': '没有提供数据'})
        
        columns = list(data.keys())
        placeholders = []
        values = []
        
        for col in columns:
            if DB_TYPE == 'mysql':
                placeholders.append('%s')
            else:
                placeholders.append('?')
            values.append(data[col])
        
        if DB_TYPE == 'mysql':
            cols_str = ', '.join([f"`{col}`" for col in columns])
            vals_str = ', '.join(placeholders)
            sql = f"INSERT INTO `{table_name}` ({cols_str}) VALUES ({vals_str})"
        elif DB_TYPE == 'mssql':
            cols_str = ', '.join([f"[{col}]" for col in columns])
            vals_str = ', '.join(placeholders)
            sql = f"INSERT INTO [{table_name}] ({cols_str}) VALUES ({vals_str})"
        else:
            cols_str = ', '.join(columns)
            vals_str = ', '.join(placeholders)
            sql = f"INSERT INTO {table_name} ({cols_str}) VALUES ({vals_str})"
        
        execute_update(sql, tuple(values))
        
        return jsonify({'success': True, 'message': '记录创建成功'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/data/<table_name>/<record_id>', methods=['PUT'])
def update_record(table_name, record_id):
    """更新记录"""
    if table_name in READONLY_TABLES:
        return jsonify({'success': False, 'error': f'表 {table_name} 是只读的，不允许更新数据'})
    
    if table_name not in TABLE_SCHEMAS:
        return jsonify({'success': False, 'error': f'表 {table_name} 不存在'})
    
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': '没有提供数据'})
        
        # 获取主键字段
        schema = TABLE_SCHEMAS[table_name]
        primary_key = None
        for col, dtype in schema.items():
            if 'PRIMARY KEY' in dtype:
                primary_key = col
                break
        
        if not primary_key:
            primary_key = 'id'  # 默认使用id字段
        
        columns = [col for col in data.keys() if col != primary_key]
        set_clause = []
        values = []
        
        for col in columns:
            if DB_TYPE == 'mysql':
                set_clause.append(f"`{col}` = %s")
            elif DB_TYPE == 'mssql':
                set_clause.append(f"[{col}] = ?")
            else:
                set_clause.append(f"{col} = ?")
            values.append(data[col])
        
        # 添加WHERE条件的值
        values.append(record_id)
        
        set_str = ', '.join(set_clause)
        
        if DB_TYPE == 'mysql':
            sql = f"UPDATE `{table_name}` SET {set_str} WHERE `{primary_key}` = %s"
        elif DB_TYPE == 'mssql':
            sql = f"UPDATE [{table_name}] SET {set_str} WHERE [{primary_key}] = ?"
        else:
            sql = f"UPDATE {table_name} SET {set_str} WHERE {primary_key} = ?"
        
        execute_update(sql, tuple(values))
        
        return jsonify({'success': True, 'message': '记录更新成功'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/data/<table_name>/<record_id>', methods=['DELETE'])
def delete_record(table_name, record_id):
    """删除记录"""
    if table_name in READONLY_TABLES:
        return jsonify({'success': False, 'error': f'表 {table_name} 是只读的，不允许删除数据'})
    
    if table_name not in TABLE_SCHEMAS:
        return jsonify({'success': False, 'error': f'表 {table_name} 不存在'})
    
    try:
        # 获取主键字段
        schema = TABLE_SCHEMAS[table_name]
        primary_key = None
        for col, dtype in schema.items():
            if 'PRIMARY KEY' in dtype:
                primary_key = col
                break
        
        if not primary_key:
            primary_key = 'id'  # 默认使用id字段
        
        if DB_TYPE == 'mysql':
            sql = f"DELETE FROM `{table_name}` WHERE `{primary_key}` = %s"
        elif DB_TYPE == 'mssql':
            sql = f"DELETE FROM [{table_name}] WHERE [{primary_key}] = ?"
        else:
            sql = f"DELETE FROM {table_name} WHERE {primary_key} = ?"
        
        execute_update(sql, (record_id,))
        
        return jsonify({'success': True, 'message': '记录删除成功'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/search/<table_name>', methods=['GET'])
def search_table(table_name):
    """搜索表数据"""
    if table_name not in TABLE_SCHEMAS:
        return jsonify({'success': False, 'error': f'表 {table_name} 不存在'})
    
    try:
        keyword = request.args.get('keyword', '')
        if not keyword:
            return get_table_data(table_name)
        
        # 构建搜索条件
        schema = TABLE_SCHEMAS[table_name]
        conditions = []
        values = [f'%{keyword}%']
        
        for col in schema.keys():
            if DB_TYPE == 'mysql':
                conditions.append(f"`{col}` LIKE %s")
            elif DB_TYPE == 'mssql':
                conditions.append(f"[{col}] LIKE ?")
            else:
                conditions.append(f"{col} LIKE ?")
        
        where_clause = ' OR '.join(conditions)
        
        if DB_TYPE == 'mysql':
            sql = f"SELECT * FROM `{table_name}` WHERE {where_clause}"
        elif DB_TYPE == 'mssql':
            sql = f"SELECT * FROM [{table_name}] WHERE {where_clause}"
        else:
            sql = f"SELECT * FROM {table_name} WHERE {where_clause}"
        
        data = execute_query(sql, tuple(values * len(conditions)))
        
        return jsonify({
            'success': True,
            'data': data,
            'total': len(data)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ==================== 启动服务 ====================
if __name__ == '__main__':
    print("=" * 50)
    print("CheapETL-UI 数据管理服务启动中...")
    print(f"数据库类型: {DB_TYPE}")
    print("=" * 50)
    
    # 初始化数据库
    init_database()
    
    # 启动Flask服务
    app.run(host='0.0.0.0', port=5000, debug=True)
