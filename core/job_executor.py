import json
import re
import subprocess
import time
import os
from config import WORK_DIR, DATAX_PY, PY_PATH
from core.models import Repo as repo


class JobExecutor:
    def __init__(self, job_id, job_type, job_template, run_params, job_log):
        self.__mode = 'prod'
        self.job_id = job_id
        self.job_type = job_type
        if job_type == 'check':
            self.job_list = repo.get_check_job(id_list_str=job_template)
        elif job_type in ('sync', 'sync_datax'):
            self.job_list = repo.get_sync_job(id_list_str=job_template)
        elif job_type == 'sql':
            self.job_list = repo.get_sql_job(id_list_str=job_template)
        else:
            raise Exception('无效作业类型')
        self.param_list = self.__parse_param(run_params)
        self.job_log = job_log

    def debug(self):
        self.__mode = 'debug'

    @staticmethod
    def __parse_param(run_params):
        param_list = []
        if isinstance(run_params, dict):
            param_list.append(run_params)
        elif isinstance(run_params, list):
            for params in run_params:
                param_list.append(params)
        else:
            param_list.append(dict())
        return param_list

    def __exe_sync_pd(self):
        e_log = {}
        for j in self.job_list:
            sub_log = []
            if len(self.param_list) > 0 and self.param_list[0] != {}:
                sync_param = self.param_list
            elif int(j['param_server_id']) != 0:
                sync_param = repo.get_job_param(server_id=str(j['param_server_id']), db_name=j['param_db_name'], sql_text=j['param_sql'])
            else:
                sync_param = [dict()]
            for p in sync_param:
                from_server_id = str(j['from_server_id'])
                if from_server_id != '' and from_server_id != 'None':
                    df = repo.read_sync_data(server_id=j['from_server_id'], db_name=j['from_db_name'], sql_text=j['from_sql'], sql_params=p)
                else:
                    df = None
                if str(j['before_write']) != '' and j['before_write'] is not None:
                    repo.exe_sql_job(server_id=j['to_server_id'], db_name=j['to_db_name'], sql_text=j['before_write'], sql_params=p)
                if df is not None and df.empty is False:
                    df = df if j['to_columns'] == '' else df[str(j['to_columns']).replace(' ', '').split(',')]
                    repo.write_sync_data(df=df, server_id=j['to_server_id'], db_name=j['to_db_name'], table_name=j['to_table'])
                if str(j['after_write']) != '' and j['after_write'] is not None:
                    repo.exe_sql_job(server_id=j['to_server_id'], db_name=j['to_db_name'], sql_text=j['after_write'], sql_params=p)
                if self.job_log:
                    try:
                        sync_rows = 'null' if df is None else len(df)
                        sub_log.append({'sync_param': str(p), 'sync_rows': str(sync_rows)})
                    except Exception as e:
                        print(e)
                        sub_log.append({'status': '日志收集出错', 'message': str(e)})
            e_log[j['id']] = sub_log
        return e_log

    def __exe_sync_datax(self):
        e_log = {}
        for j in self.job_list:
            sub_log = []
            if len(self.param_list) > 0 and self.param_list[0] != {}:
                sync_param = self.param_list
            elif int(j['param_server_id']) != 0:
                sync_param = repo.get_job_param(server_id=str(j['param_server_id']), db_name=j['param_db_name'], sql_text=j['param_sql'])
            else:
                sync_param = [dict()]
            for p in sync_param:
                from_sql = str(j['from_sql']).format(**p)
                before_write = str(j['before_write']).format(**p)
                after_write = str(j['after_write']).format(**p)
                columns = ["*"] if str(j['to_columns']).replace(' ', '') == '' else str(j['to_columns']).replace(' ', '').split(',')
                reader = repo.get_datax_reader(server_id=j['from_server_id'], db_name=j['from_db_name'], sql=from_sql)
                writer = repo.get_datax_writer(server_id=j['to_server_id'], before_write=before_write, after_write=after_write,
                                               db_name=j['to_db_name'], table_name=j['to_table'], columns=columns)

                datax_config = {"job": {
                    "setting": {"speed": {"channel": 1}, "errorLimit": {"record": 0, "percentage": 0.02}},
                    "content": [{"reader": reader, "writer": writer}]
                }}
                tmp_json_path = os.path.join(WORK_DIR, 'tmp/datax_job_' + str(time.time_ns()) + '.json')
                with open(tmp_json_path, 'w') as f:
                    json.dump(datax_config, f, indent=4)
                read_pattern = re.compile(r'读出记录总数\s+:\s+(\d+)', re.IGNORECASE)
                process = subprocess.Popen(
                    [PY_PATH, DATAX_PY, tmp_json_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    encoding='utf-8'
                )
                try:
                    read_count = -1
                    for line in process.stdout:
                        read_match = read_pattern.search(line)
                        if read_match:
                            read_count = int(read_match.group(1))
                except Exception as e:
                    print(f"读取DataX输出时出错: {e}")
                return_code = process.wait()
                if self.job_log:
                    if return_code == 0:
                        sub_log.append({'sync_param': 'datax', 'sync_rows': str(read_count)})
                        try:
                            os.remove(tmp_json_path)
                        except:
                            print(f"{tmp_json_path} 删除失败")
                    else:
                        sub_log.append({'sync_param': p, 'result': 'datax执行失败' + str(process.stdout)})
                        print(process.stdout)
                        raise Exception('datax执行失败')
            e_log[j['id']] = sub_log
        return e_log

    def __exe_sql(self):
        e_log = {}
        for j in self.job_list:
            sub_log = []
            for p in self.param_list:
                real_sql = repo.exe_sql_job(server_id=j['server_id'], db_name=j['db_name'], sql_text=j['sql_text'], sql_params=p)
                if self.job_log:
                    try:
                        sub_log.append({'sql_param': p, 'sql_text': real_sql})
                    except Exception as e:
                        print(e)
                        sub_log.append({'status': '日志收集出错', 'message': str(e)})
            e_log[j['id']] = sub_log
        return e_log

    def __exe_check(self):
        e_log = {}
        for j in self.job_list:
            sub_log = []
            for p in self.param_list:
                result_status = '不通知'
                result = repo.get_check_result(j['server_id'], j['db_name'], j['check_sql'], p)
                if result != '':
                    repo.msg(j['robot_id'], result)
                    result_status = '通知'
                if self.job_log:
                    try:
                        sub_log.append({'check_param': p, 'check_result': result_status})
                    except Exception as e:
                        print(e)
                        sub_log.append({'status': '日志收集出错', 'message': str(e)})
            e_log[j['id']] = sub_log
        return e_log

    def __exe(self):
        if self.job_type == 'sync':
            logs = self.__exe_sync_pd()
        elif self.job_type == 'sync_datax':
            logs = self.__exe_sync_datax()
        elif self.job_type == 'check':
            logs = self.__exe_check()
        elif self.job_type == 'sql':
            logs = self.__exe_sql()
        else:
            raise Exception('无效作业类型')
        return logs

    def exe(self):
        if self.__mode == 'debug':
            logs = self.__exe()
            info = json.dumps(logs, ensure_ascii=False) if self.job_log else ''
            return 0, info
        else:
            try:
                logs = self.__exe()
                info = json.dumps(logs, ensure_ascii=False) if self.job_log else ''
                return 0, info
            except Exception as e:
                return -1, e
