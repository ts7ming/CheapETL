import json
import time
from core.job_executor import JobExecutor
from core.models import Repo as repo
import logging
import argparse

logging.basicConfig(level=logging.INFO)


def main(job_type, job_id, run_params, xxl_job_id=None):
    log_id = str(time.time_ns())
    try:
        run_params_str = '' if run_params is None else json.dumps(run_params, ensure_ascii=False)
        repo.job_log_start(log_id, job_id, run_params_str)
        je = JobExecutor(job_id, job_type, run_params, 1)
        code, msg = je.exe()
    except Exception as e:
        repo.admin_err(xxl_job_id=xxl_job_id, job_id=job_id, job_type=job_type, err_msg=str(e))
        logging.error(str(e))
        return None

    if code == 0:
        repo.job_log_end(log_id, 3, msg)
    else:
        repo.job_log_end(log_id, -1, msg)
        repo.admin_err(xxl_job_id=xxl_job_id, job_id=job_id, job_type=job_type, err_msg=str(msg))
        logging.error(str(msg))


def parse_args():
    parser = argparse.ArgumentParser(description='任务执行脚本')

    parser.add_argument('--job_type', required=True,
                        choices=['sync', 'sync_datax', 'sql', 'check'],
                        help='任务类型，可选值: sync, sync_datax, sql, check')
    parser.add_argument('--job_id', required=True,
                        help='任务ID')

    parser.add_argument('--xxl_job_id', required=False,
                        help='XXL任务ID')

    args, unknown = parser.parse_known_args()

    run_params = {}
    i = 0
    while i < len(unknown):
        if unknown[i].startswith('--') and i + 1 < len(unknown):
            key = unknown[i][2:]
            value = unknown[i + 1]
            run_params[key] = value
            i += 2
        else:
            i += 1
    return {
        'job_type': args.job_type,
        'job_id': args.job_id,
        'xxl_job_id': args.xxl_job_id,
        'run_params': run_params
    }


if __name__ == '__main__':
    params = parse_args()

    p_job_type = str(params['job_type'])
    p_job_id = str(params['job_id'])
    p_xxl_job_id = params['xxl_job_id']
    p_run_params = params['run_params']
    logging.info("=" * 30 + ' 执行参数 ' + "=" * 30)
    logging.info(f'任务类型: {p_job_type}')
    logging.info(f'任务ID: {p_job_id}')
    if p_xxl_job_id:
        logging.info(f'XXL任务ID: {p_xxl_job_id}')
    logging.info(f'任务参数: {p_run_params}')
    logging.info("=" * 30 + ' 开始执行 ' + "=" * 30)
    main(p_job_type, p_job_id, p_run_params, p_xxl_job_id)
    logging.info("=" * 30 + ' 执行完成 ' + "=" * 30)
