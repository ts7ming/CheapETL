# CheapETL


### 使用步骤
#### 1. 下载代码
-  `git clone https://github.com/ts7ming/CheapETL`
- (或 `git clone https://gitee.com/ts7ming/CheapETL`)
#### 2. 准备环境
- 在MySQL执行 `etl.sql`
- 创建 `settings.py`

    ```python
    DS_CONFIG = {
        'conn_type': 'mysql',
        'host': 'localhost', 
        'username': 'root', 
        'password': 'qiming', 
        'port': '3306', 
        'db_name': 'dw'
    }
    WORK_DIR = '/app/CheapETL/'
    DATAX_PY = '/opt/datax/bin/data.py'
    PY_PATH = 'python3'
    ```
#### 3. 添加数据源
- 在 MySQL `etl_server` 表添加数据源id和连接信息
    - 如果用datax写入 doris, 需要单独新建数据源id, port值为  `fe_port,be_port` 例如 `9030,8030`

#### 4. 配置同步任务
- 在 MySQL `etl_job_sync` 表添加同步配置

#### 5. 执行同步任务
- 通过 **xxl-job**, **crontab** 或其他方式执行 `python3 script_path sync_id param`
    - 数据量小的同步: `script_path` = `/app/CheapETL/sync.py`
    - 数据量大的同步: `script_path` = `/app/CheapETL/sync_datax.py`
    - `sync_id` = `etl_job_sync.id`
    - param是指定参数, 优先级高于 `etl_job_sync.param_sql`
- 例如: `python3 /app/CheapETL/sync_datax.py 2001`
- 例如: `python3 /app/CheapETL/sync.py 2002 --start_date "$(date -d '-1 day' +%Y-%m-%d)" --end_date "$(date +%Y-%m-%d)"`