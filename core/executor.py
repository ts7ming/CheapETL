import importlib
import json
import re
import subprocess
import time
import os
from config import WORK_DIR, DATAX_PY
from core import repo, print_log
from pyqueen import DataSource


class JobExecutor:
    def __init__(self, job_type, job_template, run_params, job_log):
        self.job_type = job_type
        if job_type == 'py':
            self.job_list = repo.get_py_job(id_list_str=job_template)
        elif job_type == 'check':
            self.job_list = repo.get_check_job(id_list_str=job_template)
        elif job_type in ('sync', 'sync_pd', 'sync_datax'):
            self.job_list = repo.get_sync_job(id_list_str=job_template)
        elif job_type == 'sql':
            self.job_list = repo.get_sql_job(id_list_str=job_template)
        else:
            raise Exception('无效作业类型')
        self.param_list = self.__parse_param(run_params)
        self.job_log = job_log

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

    def __import_py(self, py_path):
        if not os.path.exists(py_path):
            raise FileNotFoundError(f"脚本不存在: {py_path}")
        module_name = os.path.basename(py_path).split(".")[0]
        spec = importlib.util.spec_from_file_location(module_name, py_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if self.job_log:
            try:
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, DataSource):
                        attr.record_log(field_list=['func_name', 'start_time', 'end_time', 'sql_text', 'server_id', 'db_name', 'table_name'])
            except Exception as e:
                print_log('日志设置出错: ' + str(e))
        return module

    def __exe_py(self):
        e_log = {}
        for j in self.job_list:
            module = self.__import_py(os.path.join(WORK_DIR, j['py_path']))
            sub_log = []
            for p in self.param_list:
                module.main(**p)
                if self.job_log:
                    try:
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            if isinstance(attr, DataSource):
                                sub_log.extend(attr.export_log())
                    except Exception as e:
                        print_log(e)
                        sub_log.append({'status': '日志收集出错', 'message': str(e)})
            e_log[j['py_path']] = sub_log
        return e_log

    def __exe_sync_pd(self):
        e_log = {}
        for j in self.job_list:
            sub_log = []
            for p in self.param_list:
                from_server = str(j['from_server'])
                if from_server != '' and from_server != 'None':
                    df = repo.read_sync_data(server_id=j['from_server'], db_name=j['from_db'], sql_text=j['from_sql'], sql_params=p)
                else:
                    df = None
                if j['before_write'] != '':
                    repo.exe_sync_sql(server_id=j['to_server'], db_name=j['to_db'], sql_text=j['before_write'], sql_params=p)
                if df is not None:
                    df = df if j['to_columns'] == '' else df[str(j['to_columns']).replace(' ','').split(',')]
                    repo.write_sync_data(df=df, server_id=j['to_server'], db_name=j['to_db'], table_name=j['to_table'])
                if self.job_log:
                    try:
                        sync_rows = 'null' if df is None else len(df)
                        sub_log.append({'sync_param': p, 'sync_rows': str(sync_rows)})
                    except Exception as e:
                        print_log(e)
                        sub_log.append({'status': '日志收集出错', 'message': str(e)})
            e_log[j['id']] = sub_log
        return e_log
    
    def __exe_sync_datax(self):
        e_log = {}
        for j in self.job_list:
            sub_log = []
            for p in self.param_list:
                from_sql = str(j['from_sql']).format(**p)
                before_write = str(j['before_write']).format(**p)
                columns = ["*"] if str(j['to_columns']).replace(' ','') == '' else str(j['to_columns']).replace(' ','').split(',')
                reader = repo.get_datax_reader(server_id=j['from_server'],db_name=j['from_db'],sql=from_sql)
                writer = repo.get_datax_writer(server_id=j['to_server'], before_write=before_write,db_name=j['to_db'], table_name=j['to_table'],columns=columns)

                datax_config = {"job": {
                    "setting": {"speed": {"channel": 1},"errorLimit": {"record": 0,"percentage": 0.02}},
                    "content": [{"reader": reader,"writer": writer}]
                }}
                tmp_json_path = os.path.join(WORK_DIR, 'tmp/datax_job_'+ str(time.time_ns())+'.json')
                with open(tmp_json_path, 'w') as f:
                    json.dump(datax_config, f, indent=4)
                read_pattern = re.compile(r'读出记录总数\s+:\s+(\d+)', re.IGNORECASE)
                process = subprocess.Popen(
                    ['python3', DATAX_PY, tmp_json_path], 
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
                    print_log(f"读取DataX输出时出错: {e}")
                return_code = process.wait()
                if self.job_log:
                    if return_code == 0:
                        sub_log.append({'sync_param': 'datax', 'sync_rows': str(read_count)})
                        try:
                            os.remove(tmp_json_path)
                        except:
                            print_log(f"{tmp_json_path} 删除失败")
                    else:
                        sub_log.append({'sync_param': p, 'result': 'datax执行失败'})
                        print_log(process.stderr) #报错写入 /log/yyyymm.log
                        raise Exception('datax执行失败')
            e_log[j['id']] = sub_log
        return e_log

    def __exe_sql(self):
        e_log = {}
        for j in self.job_list:
            sub_log = []
            for p in self.param_list:
                repo.exe_sql_job(server_id=j['server_id'], db_name=j['db_name'], sql_text=j['sql_text'], sql_params=p)
                if self.job_log:
                    try:
                        sub_log.append({'sql_param': p})
                    except Exception as e:
                        print_log(e)
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
                        print_log(e)
                        sub_log.append({'status': '日志收集出错', 'message': str(e)})
            e_log[j['id']] = sub_log
        return e_log

    def exe(self):
        try:
            if self.job_type == 'py':
                logs = self.__exe_py()
            elif self.job_type == 'sync' or self.job_type == 'sync_pd':
                logs = self.__exe_sync_pd()
            elif self.job_type == 'sync_datax':
                logs = self.__exe_sync_datax()
            elif self.job_type == 'check':
                logs = self.__exe_check()
            elif self.job_type == 'sql':
                logs = self.__exe_sql()
            else:
                raise Exception('无效作业类型')
            info = json.dumps(logs, ensure_ascii=False) if self.job_log else ''
            return 0, info
        except Exception as e:
            return -1, e

    def debug(self):
        if self.job_type == 'py':
            logs = self.__exe_py()
        elif self.job_type == 'sync' or self.job_type == 'sync_pd':
            logs = self.__exe_sync_pd()
        elif self.job_type == 'sync_datax':
            logs = self.__exe_sync_datax()
        elif self.job_type == 'check':
            logs = self.__exe_check()
        elif self.job_type == 'sql':
            logs = self.__exe_sql()
        else:
            raise Exception('无效作业类型')
        info = json.dumps(logs, ensure_ascii=False) if self.job_log else ''
        return 0, info
