from pyqueen import DataSource
from settings import *
import os


ds_cfg = DataSource(**DS_CONFIG)
DATABASES = {}

tmp_db = {}
sql = f'select server_id,conn_type,host,username,password,port,db_name from etl_server'
df = ds_cfg.read_sql(sql)
for server_id, conn_type, host, username, password, port, db_name in df.values:
    DATABASES[str(server_id)] = {
        'conn_type': conn_type,
        'host': host,
        'username': username,
        'password': str(password),
        'port': port,
        'db_name': db_name
    }

tmp_dir = os.path.join(WORK_DIR, 'tmp')
if not os.path.exists(tmp_dir):
    os.makedirs(tmp_dir)