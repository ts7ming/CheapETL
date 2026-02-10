import json
import time
from core import repo, print_log
from core.job_executor import JobExecutor
from pyqueen import TimeKit  # 构建参数用
import multiprocessing
from config import PARALLELISM


class JobInstance:
    def __init__(self, job_info):
        self.__mode = 'prod'
        self.log_id = None
        self.job_id = str(job_info['id'])
        self.job_params = job_info['job_params']
        self.message_robot = job_info['message_robot']
        self.job_log = True if str(job_info['job_log']) == '1' else False
        self.job_message = True if str(job_info['job_message']) == '1' else False
        self.job_type = job_info['job_type']
        self.job_template = job_info['job_template']
        self.job_name = job_info['job_name']
        self.job_on_error = int(job_info['job_on_error'])

    def debug(self):
        self.__mode = 'debug'

    @staticmethod
    def __build_params(job_params):
        """
        字符串参数解析成python对象
        单层字典参数, 每个值都可以使用TimeKit辅助生成参数值
        列表参数, 每个元素为单层字典
        :param job_params: {"p1":"v1"}  or [{"p1":"v1"},{"p1":"v2"},{"p1":"v3"}]
        :return:
        """
        if job_params is None or job_params == '' or str(job_params) == 'None':
            return None
        job_params = json.loads(job_params)
        if isinstance(job_params, list):
            real_params = []
            for params in job_params:
                tmp = {}
                for k, v in params.items():
                    code_str = 'tk=TimeKit()\ncfg=repo.get_cfg\netl_job_params=' + str(v)
                    variables = {}
                    try:
                        exec(code_str, None, variables)
                        tmp[k] = variables['etl_job_params']
                    except Exception as e:
                        print_log(e)
                real_params.append(tmp)
        elif isinstance(job_params, dict):
            real_params = {}
            for k, v in job_params.items():
                code_str = 'tk=TimeKit()\ncfg=repo.get_cfg\netl_job_params=' + str(v)
                variables = {}
                try:
                    exec(code_str, None, variables)
                    real_params[k] = variables['etl_job_params']
                except Exception as e:
                    print_log(e)
        else:
            raise Exception('无效参数')
        return real_params

    def run(self):
        run_params = self.__build_params(self.job_params)  # 构建运行参数
        repo.register_job_start(self.job_id)
        if self.job_log:
            self.log_id = str(time.time_ns())
            run_params_str = '' if run_params is None else json.dumps(run_params, ensure_ascii=False)
            repo.job_log_start(self.log_id, self.job_id, run_params_str)
        je = JobExecutor(self.job_id, self.job_type, self.job_template, run_params, self.job_log)
        if self.__mode == 'debug':
            je.debug()
        code, msg = je.exe()
        # 根据执行结果记录日志和发送提醒
        if code == 0:
            repo.register_job_end(self.job_id)
            if self.job_log:
                repo.job_log_end(self.log_id, 3, msg)
            if self.job_message:
                run_params_str = '' if run_params is None else json.dumps(run_params, ensure_ascii=False)
                repo.msg(self.message_robot, '通知: 任务执行完成\n\n【' + self.job_name + '】\n【' + run_params_str + '】')
        else:
            repo.register_job_error(self.job_id)
            if self.job_log:
                repo.job_log_end(self.log_id, -1, msg)
            repo.admin_msg(text='ETL任务 ' + str(self.job_name) + '\n执行出错\n\n' + str(msg)[0:100])
            print_log(msg)
        # 后序job
        if self.__mode == 'debug' or (code == -1 and self.job_on_error == 1):
            print_log('跳过后续任务')
            return []
        # 后序任务
        follow_job_list = repo.get_follow_job(self.job_id)

        # 如果前任务是 flink-batch任务, 等待集群执行完成后再执行后序任务
        if self.job_type == 'flink-batch':
            df = repo.get_flink_job_running(job_id=str(self.job_id))
            running = True
            while running:
                time.sleep(5)
                running = False
                for id, flink_job_id in df[['id','flink_job_id']].values:
                    status, duration = repo.get_flink_job_status(str(flink_job_id))
                    if status == 1 or status == 2:
                        running = True
                        continue
                    if status == -1 and duration == -1:
                        repo.update_flink_job_error(str(id))
                    else:
                        repo.update_flink_job_finish(id, status, str(duration))
        if len(follow_job_list) == 0:
            return []
        else:
            return follow_job_list


class JobManager:
    @staticmethod
    def schedule(user_job_list=None, mode='prod'):
        job_list = repo.get_job(user_job_list)
        if len(job_list) == 0:
            print_log('----------------------------------------------------')
            print_log('没有任务')
            exit()
        parallelism = int(PARALLELISM)
        while len(job_list) > 0:
            repo.register_job_pending(job_list)
            current_jobs = []
            for _ in range(min(parallelism, len(job_list))):
                current_jobs.append(job_list.pop(0))
            with multiprocessing.Pool(processes=parallelism) as pool:
                results = []
                for job_info in current_jobs:
                    serializable_job_info = job_info.copy()
                    results.append(pool.apply_async(JobManager._run_job_process, (serializable_job_info, mode)))
                for result in results:
                    try:
                        re = result.get()
                        job_list.extend(re)
                    except Exception as e:
                        print_log(f"任务执行出错: {e}")
    @staticmethod
    def _run_job_process(job_info, mode):
        job_instance = JobInstance(job_info)
        if mode == 'debug':
            job_instance.debug()
        print_log('----------------------------------------------------')
        print_log(job_info)
        return job_instance.run()
