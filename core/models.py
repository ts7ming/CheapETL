from pyqueen import DataSource, TimeKit, Dingtalk
import time
import re
from core.utils import parse_xxl_job
from config import (
    ds_cfg,
    DATABASES,
    ADMIN_ROBOT,
    ROBOTS,
    T_JOB_LOG,
    T_CHECK,
    T_SYNC,
    T_SQL,
    T_MESSAGE,
    T_ERR_HANDLING_CFG
)

ds = ds_cfg


class Repo:
    @staticmethod
    def get_datax_reader(server_id, db_name, sql):
        server_cfg = DATABASES[str(server_id)]
        if server_cfg['conn_type'] == 'oracle':
            reader = 'oraclereader'
            url = "jdbc:oracle:thin:@{host}:{port}:{db_name}"
        elif server_cfg['conn_type'] == 'mssql':
            reader = 'sqlserverreader'
            url = "jdbc:sqlserver://{host}:{port};DatabaseName={db_name}"
        elif server_cfg['conn_type'] == 'mysql':
            reader = 'mysqlreader'
            url = "jdbc:mysql://{host}:{port}/{db_name}"
        else:
            raise Exception('未知类型')
        url = url.format(host=server_cfg['host'], port=server_cfg['port'], db_name=db_name)
        cfg = {
            "name": reader,
            "parameter": {
                "username": server_cfg['username'],
                "password": server_cfg['password'],
                "connection": [{"querySql": [sql], "jdbcUrl": [url]}]
            }
        }
        return cfg

    @staticmethod
    def get_datax_writer(server_id, before_write, after_write, db_name, table_name, columns=["*"]):
        if str(before_write) == 'None' or before_write is None:
            before_write = ''
        if str(after_write) == 'None' or after_write is None:
            after_write = ''
        server_cfg = DATABASES[str(server_id)]
        port = str(server_cfg['port'])
        if server_cfg['conn_type'] == 'oracle':
            writer = 'oraclewriter'
            url = "jdbc:oracle:thin:@{host}:{port}:{db_name}"
        elif server_cfg['conn_type'] == 'mssql':
            writer = 'sqlserverwriter'
            url = "jdbc:sqlserver://{host}:{port};DatabaseName={db_name}"
        elif server_cfg['conn_type'] == 'mysql':
            writer = 'mysqlwriter'
            url = "jdbc:mysql://{host}:{port}/{db_name}?useUnicode=true&characterEncoding=utf8"
        elif server_cfg['conn_type'] == 'doris':
            writer = 'doriswriter'
            url = "jdbc:mysql://{host}:{port}/{db_name}?useUnicode=true&characterEncoding=utf8"
            port = str(server_cfg['port']).split(',')[0]
            port_be = str(server_cfg['port']).split(',')[1]
        else:
            raise Exception('未知类型')
        url = url.format(host=server_cfg['host'], port=port, db_name=db_name)
        connection = [{"jdbcUrl": url, "table": [table_name]}]
        parameter = {
            "username": server_cfg['username'],
            "password": server_cfg['password'],
            "column": columns,
            "preSql": [before_write],
            "postSql": [after_write],
            "connection": connection
        }
        if server_cfg['conn_type'] == 'doris':
            parameter = {
                "username": server_cfg['username'],
                "password": server_cfg['password'],
                "column": columns,
                "preSql": [before_write],
                "connection": [{"jdbcUrl": url, "table": [table_name], "selectedDatabase": db_name}],
                "loadUrl": [server_cfg['host'] + ':' + port_be],
            }
        cfg = {
            "name": writer,
            "parameter": parameter
        }
        return cfg

    @staticmethod
    def msg_log(robot_id, text):
        tk = TimeKit()
        now = tk.int2str(tk.now)
        try:
            text = text.replace("'", '"')
            sql = f'''insert into {T_MESSAGE} (robot_id, send_time, text) VALUES ('{robot_id}', '{now}', '{text}')'''
            ds.exe_sql(sql)
        except Exception as e:
            print(e)

    @staticmethod
    def msg(robot_id, text):
        time.sleep(1)
        robot_id = str(robot_id)
        if ',' in robot_id:
            robot_list = robot_id.split(',')
        else:
            robot_list = [robot_id]
        for rbt in robot_list:
            ding = Dingtalk(**ROBOTS[rbt])
            ding.send(content=text)
            Repo.msg_log(rbt, text)

    @staticmethod
    def get_error_handle(err_msg):
        sql = '''
            SELECT
                id,
                error_pattern,
                action_type,
                action_params 
            FROM
                {T_ERR_HANDLING_CFG}
        '''
        rule_id, action = None, None
        try:
            df = ds.read_sql(sql)
            for eid, error_pattern, action_type, action_params in df[['id', 'error_pattern', 'action_type', 'action_params']].values:
                if re.search(error_pattern, err_msg):
                    if action_type == 'message':
                        rule_id = str(eid)
                        action = str(action_params)
                        break
        except:
            pass
        return rule_id, action


    @staticmethod
    def get_xxl_job_conf():
        try:
            from config import XXL_JOB_DB_ID
        except:
            print('没有配置 settings.XXL_JOB_DB_ID')
            return None
        if XXL_JOB_DB_ID is None or XXL_JOB_DB_ID not in DATABASES:
            return None
        ds_xj = DataSource(**DATABASES[XXL_JOB_DB_ID])
        sql = '''
            SELECT id, child_jobid, schedule_conf,glue_source,job_desc
            FROM xxl_job.xxl_job_info
        '''
        df = ds_xj.read_sql(sql)
        return df

    @staticmethod
    def admin_err(xxl_job_id, job_id, job_type, err_msg):
        err = f'**任务类型**: {job_type}'

        time.sleep(1)
        rule_id, action = Repo.get_error_handle(err_msg)
        info = {}
        if xxl_job_id is not None:
            try:
                info = parse_xxl_job(df=Repo.get_xxl_job_conf(), xxl_job_id=str(xxl_job_id))
                err += f'\n\n**xxl_job_id**: {xxl_job_id}'
            except:
                print('解析xxl-job依赖出错')
        err += f'\n\n**job_id**: {job_id}'
        if 'job_desc' in info:
            job_desc = info['job_desc']
            err += f'\n\n**任务名称**: {job_desc}'

        if 'job_tracking' in info:
            job_tracking = ' <- '.join(info['job_tracking'])
            err += f'\n\n**任务调用链**: {job_tracking}'

        if 'next_time' in info:
            next_time = info['next_time']
            err += f'\n\n**下次执行时间**: {next_time}'
        if rule_id is not None:
            err += f'\n\n**报错匹配**: 规则({rule_id}) {action}'
            err_msg = err_msg[0:20] + '...'
        else:
            err_msg = err_msg[0:300]
        err += f'\n\n**报错信息**: {err_msg}'

        ding = Dingtalk(**ADMIN_ROBOT)
        ding.send_markdown(title='任务出错', text=err)

    @staticmethod
    def job_log_start(log_id, job_id, run_params_str):
        tk = TimeKit()
        now = tk.int2str(tk.now)
        try:
            sql = f"insert into {T_JOB_LOG} (id, job_id, execution_status, start_time, job_params) values ('{log_id}','{job_id}',2,'{now}','{run_params_str}')"
            ds.exe_sql(sql)
        except Exception as e:
            print(e)

    @staticmethod
    def job_log_end(log_id, status, msg):
        tk = TimeKit()
        now = tk.int2str(tk.now)
        try:
            if msg is None:
                sql2 = f'''update {T_JOB_LOG} set execution_status={status}, end_time = '{now}' where id ='{log_id}' '''
            else:
                msg = str(msg).replace("'", "''").replace('\n', '    ')
                sql2 = f'''update {T_JOB_LOG} set execution_status={status}, message='{msg}', end_time = '{now}' where id ='{log_id}' '''
            ds.exe_sql(sql2)
        except Exception as e:
            print(e)

    @staticmethod
    def get_check_job(id_list_str):
        sql = f'''
        SELECT id, server_id, db_name, check_sql, robot_id
        FROM {T_CHECK}
        WHERE id in ({id_list_str})
        '''
        df = ds.read_sql(sql)

        tk = TimeKit()
        now = tk.int2str(tk.now)
        try:
            register_sql = f"update {T_CHECK} set last_execution_time='{now}' WHERE id in ({id_list_str})"
            ds.exe_sql(register_sql)
        except Exception as e:
            print("更新子任务调用记录失败: " + str(e))
        return df.to_dict('records')

    @staticmethod
    def get_check_result(server_id, db_name, check_sql, run_params):
        ds_tgt = DataSource(**DATABASES[str(server_id)])
        ds_tgt.set_db(db_name)
        check_sql = check_sql.format(**run_params)
        v = ds_tgt.get_value(check_sql)
        v = v.replace("$rn", "\n")
        return str(v)

    @staticmethod
    def get_sync_job(id_list_str):
        sql = f'''
        SELECT id, ifnull(param_server_id,0) as param_server_id,param_db_name,param_sql,from_server_id,from_db_name, from_sql, to_server_id, to_db_name, to_table, to_columns, before_write, after_write
        FROM {T_SYNC}
        WHERE id in ({id_list_str})
        '''
        df = ds.read_sql(sql)
        records = df.to_dict('records')
        id_list = [id.strip() for id in id_list_str.split(',')]
        ordered_records = sorted(records, key=lambda x: id_list.index(str(x['id'])))

        tk = TimeKit()
        now = tk.int2str(tk.now)
        try:
            register_sql = f"update {T_SYNC} set last_execution_time='{now}' WHERE id in ({id_list_str})"
            ds.exe_sql(register_sql)
        except Exception as e:
            print("更新子任务调用记录失败: " + str(e))
        return ordered_records

    @staticmethod
    def get_job_param(server_id, db_name, sql_text):
        tmp_ds = DataSource(**DATABASES[str(server_id)])
        tmp_ds.set_db(db_name)
        df = tmp_ds.read_sql(sql_text)
        df = df.head(1)
        param = df.to_dict('records')
        return param

    @staticmethod
    def get_sql_job(id_list_str):
        sql = f'''
        SELECT id, server_id, db_name, sql_text
        FROM {T_SQL}
        WHERE id in ({id_list_str})
        '''
        df = ds.read_sql(sql)
        records = df.to_dict('records')
        id_list = [id.strip() for id in id_list_str.split(',')]
        ordered_records = sorted(records, key=lambda x: id_list.index(str(x['id'])))

        tk = TimeKit()
        now = tk.int2str(tk.now)
        try:
            register_sql = f"update {T_SQL} set last_execution_time='{now}' WHERE id in ({id_list_str})"
            ds.exe_sql(register_sql)
        except Exception as e:
            print("更新子任务调用记录失败: " + str(e))

        return ordered_records

    @staticmethod
    def read_sync_data(server_id, db_name, sql_text, sql_params):
        ds_sync = DataSource(**DATABASES[str(server_id)])
        ds_sync.set_db(db_name)
        df = ds_sync.read_sql(sql_text.format(**sql_params))
        return df

    @staticmethod
    def write_sync_data(df, server_id, db_name, table_name):
        ds_sync = DataSource(**DATABASES[str(server_id)])
        if ds_sync.conn_type == 'oracle':
            info = db_name.split('.')
            schema = info[0]
            db_name = info[1]
        ds_sync.set_db(db_name)
        if df is not None:
            if ds_sync.conn_type == 'oracle':
                ds_sync.to_db(df, table_name, schema=schema)
            else:
                ds_sync.to_db(df, table_name)

    @staticmethod
    def exe_sql_job(server_id, db_name, sql_text, sql_params):
        ds = DataSource(**DATABASES[str(server_id)])
        if ds.conn_type == 'oracle':
            info = db_name.split('.')
            schema = info[0]
            db_name = info[1]
        ds.set_db(db_name)
        if sql_params is None:
            real_sql = sql_text
        else:
            real_sql = sql_text.format(**sql_params)

        if '----------' in str(real_sql):
            ds.set('keep_conn', True)
            sql_list = real_sql.split('----------')
            for sub_sql in sql_list:
                ds.exe_sql(sub_sql)
            try:
                ds.close_conn()
            except:
                pass
        else:
            ds.exe_sql(real_sql)

        return real_sql
