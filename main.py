import sys
from core.job_manager import JobManager as jm
from core import repo


def main(user_job_list):
    if len(user_job_list) == 0:
        user_job_list = None
    try:
        jm.schedule(user_job_list=user_job_list)
    except Exception as e:
        repo.admin_msg(text='调度出错\n\n' + str(e)[0:500])


if __name__ == '__main__':
    job_list = sys.argv[1:]
    main(job_list)
