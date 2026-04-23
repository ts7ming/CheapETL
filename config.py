from pyqueen import DataSource
from settings import *
import os

try:
    ds_cfg = DataSource(**DS_CONFIG)
except:
    print('没有设置配置数据库')
    ds_cfg = None


if ds_cfg is not None:
    tmp_db = {}
    sql = f'select server_id,conn_type,host,username,password,port,db_name from etl_server'
    df = ds_cfg.read_sql(sql)
    for server_id, conn_type, host, username, password, port, db_name in df.values:
        if str(server_id) not in DATABASES:
            tmp_db[str(server_id)] = {
                'conn_type': conn_type,
                'host': host,
                'username': username,
                'password': password,
                'port': port,
                'db_name': db_name
            }
    for k, v in tmp_db.items():
        if k not in DATABASES.keys():
            DATABASES[k] = v

if ds_cfg is not None:
    sql = 'select robot_id, access_token, secret from etl_robot'
    df = ds_cfg.read_sql(sql)
    for robot_id, access_token, secret in df.values:
        if str(robot_id) not in ROBOTS:
            ROBOTS[str(robot_id)] = {
                'access_token': access_token,
                'secret': secret
            }
