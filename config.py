import os

from pyqueen import DataSource
from core.utils import decrypt, encrypt

# --------------------------  配置优先级  --------------------------
# 优先取 settings.py 的值, 如果没有尝试从数据库配置表获取

# --------------------------  配置文件导入  --------------------------
try:
    import settings
except ImportError:
    settings = None

# --------------------------  配置库  -----------------------------
ds_cfg = DataSource(**settings.DS_CONFIG) if hasattr(settings, 'DS_CONFIG') else None

# --------------------------  配置表表名  --------------------------
T_SERVER = getattr(settings, 'T_SERVER', 'etl_server')
T_JOB = getattr(settings, 'T_JOB', 'etl_job')
T_JOB_LOG = getattr(settings, 'T_JOB_LOG', 'etl_log')
T_CHECK = getattr(settings, 'T_CHECK', 'etl_job_check')
T_SYNC = getattr(settings, 'T_SYNC', 'etl_job_sync')
T_PY = getattr(settings, 'T_PY', 'etl_job_py')
T_SQL = getattr(settings, 'T_SQL', 'etl_job_sql')
T_MESSAGE = getattr(settings, 'T_MESSAGE', 'etl_robot_message')
T_DICT = getattr(settings, 'T_DICT', 'etl_dict')
T_RPT_PUB = getattr(settings, 'T_RPT_PUB', 'etl_rpt_publish')
T_USER_REQUEST = getattr(settings, 'T_USER_REQUEST', 'etl_user_request')

# --------------------------  环境参数  ----------------------------
SECRET_KEY = getattr(settings, 'SECRET_KEY', 'SECRET_KEY')
WORK_DIR = getattr(settings, 'WORK_DIR', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENVIRONMENT_VARIABLE = getattr(settings, 'ENVIRONMENT_VARIABLE', [])
FINEREPORT_DIR = getattr(settings, 'FINEREPORT_DIR', None)
DATAX_PY = getattr(settings, 'DATAX_PY', None)

# --------------------------  数据连接  ----------------------------
if hasattr(settings, 'DATABASES'):
    DATABASES = settings.DATABASES
else:
    DATABASES = {}
    if ds_cfg is not None:
        sql = f'select server_id,conn_type,host,username,password,port,db_name from {T_SERVER}'
        df = ds_cfg.read_sql(sql)
        for server_id, conn_type, host, username, password, port, db_name in df.values:
            DATABASES[str(server_id)] = {
                'conn_type': conn_type,
                'host': host,
                'username': username,
                'password': decrypt(password, SECRET_KEY),
                'port': port,
                'db_name': db_name
            }

# --------------------------  通知机器人  ----------------------------
if hasattr(settings, 'ROBOTS'):
    ROBOTS = settings.ROBOTS
else:
    ROBOTS = {}
    if ds_cfg is not None:
        sql = '''
        select robot_id, access_token, secret
        from etl_robot
        '''
        df = ds_cfg.read_sql(sql)
        for robot_id, access_token, secret in df.values:
            ROBOTS[str(robot_id)] = {
                'access_token': access_token,
                'secret': secret
            }

if __name__ == '__main__':
    pw = input('password:')
    pw = str(pw).strip()
    epw = encrypt(pw, SECRET_KEY)
    if decrypt(epw, SECRET_KEY) == pw:
        print(f'encrypt password: "{epw}"')
    else:
        print('校验失败')
