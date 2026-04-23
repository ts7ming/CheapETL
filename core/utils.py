import pandas as pd
from croniter import croniter
from datetime import datetime
from typing import Optional, Tuple, List
import re


def convert_quartz_to_standard_cron(quartz_cron: str) -> str:
    if not quartz_cron or quartz_cron.strip() == '':
        return quartz_cron

    quartz_cron = quartz_cron.replace('?', '*').strip()

    fields = quartz_cron.split()

    if len(fields) >= 6:
        fields = fields[1:]
        if len(fields) == 6:
            fields = fields[:5]

    return ' '.join(fields)


def parse_xxl_job(df: pd.DataFrame, xxl_job_id: str) -> Tuple[Optional[datetime], List[str]]:
    current_time = datetime.now()
    info = {'xxl_job_id':xxl_job_id}

    job_tracking = [xxl_job_id]
    visited_tasks = set()

    iteration_count = 0
    max_iterations = 100
    matched_rows = df[df['id'].astype(int) == int(xxl_job_id)]
    if matched_rows.empty:
        return info
    current_row = matched_rows.iloc[0]
    info['job_desc'] = current_row['job_desc']

    while xxl_job_id not in visited_tasks:
        iteration_count += 1
        if iteration_count > max_iterations:
            info['job_tracking'] = job_tracking
            return info
        visited_tasks.add(xxl_job_id)
        schedule_conf = current_row['schedule_conf']
        has_schedule = False
        if pd.notna(schedule_conf):
            schedule_str = str(schedule_conf).strip()
            if schedule_str and schedule_str.lower() != 'nan':
                has_schedule = True

        if has_schedule:
            try:
                cron_str = str(schedule_conf).strip()
                cron_str = convert_quartz_to_standard_cron(cron_str)
                cron = croniter(cron_str, current_time)
                next_time = cron.get_next(datetime)
                if str(xxl_job_id) not in job_tracking:
                    job_tracking.append(str(xxl_job_id))
                info['job_tracking'] = job_tracking
                info['next_time'] = next_time
                return info
            except Exception:
                return info

        def match_child_jobid(child_str):
            if pd.isna(child_str):
                return False
            child_list = [x.strip() for x in str(child_str).split(',')]
            return str(xxl_job_id) in child_list

        parent_rows = df[df['child_jobid'].apply(match_child_jobid)]
        if parent_rows.empty:
            info['job_tracking'] = job_tracking
            return info
        parent_id = parent_rows.iloc[0]['id']
        if parent_id == xxl_job_id:
            info['job_tracking'] = job_tracking
            return info
        if str(parent_id) not in job_tracking:
            job_tracking.append(str(parent_id))
        current_row = parent_rows.iloc[0]
        xxl_job_id = parent_id
    info['job_tracking'] = job_tracking
