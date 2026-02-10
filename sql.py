import json
import sys
import time
from core.job_executor import JobExecutor
from core import repo
import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)
def main(sql_id, run_params):
    log_id = str(time.time_ns())
    try:
        run_params_str = '' if run_params is None else json.dumps(run_params, ensure_ascii=False)
        repo.job_log_start_new(log_id, sql_id, run_params_str)
        je = JobExecutor(sql_id, 'sql', str(sql_id), run_params, 1)
        code, msg = je.exe()
    except Exception as e:
        repo.admin_msg(text='SQL任务 ' + str(sql_id) + '\n执行出错\n\n' + str(e)[0:300])
        logger.error(str(e))
        return None

    if code == 0:
        repo.register_job_end(sql_id)
        repo.job_log_end(log_id, 3, msg)
    else:
        repo.register_job_error(sql_id)
        repo.job_log_end(log_id, -1, msg)
        repo.admin_msg(text='SQL任务 ' + str(sql_id) + '\状态错误\n\n' + str(msg)[0:300])
        logger.error(str(msg))

if __name__ == '__main__':
    if len(sys.argv) >= 2:
        try:
            sql_id = int(sys.argv[1])
            dynamic_args = sys.argv[2:]
            run_params = {k.lstrip('-'): v for k, v in zip(dynamic_args[::2], dynamic_args[1::2])}
        except (ValueError, IndexError) as e:
            print(f"参数错误: {e}", file=sys.stderr)
            logger.error(str(e))
            sys.exit(1)
    else:
        run_params = None
    logger.info("============================   开始执行   ============================")
    logger.info('同步参数: '+str(run_params))
    main(sql_id, run_params)
    logger.info("============================   执行完成   ============================")