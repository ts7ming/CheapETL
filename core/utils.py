from pyqueen import TimeKit


def print_log(text):
    tk = TimeKit()
    print(tk.int2str(tk.now) + ' ' + str(text))


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


# if __name__ == "__main__":
#     df = pd.read_excel('d://aa.xlsx')
#     xxl_job_id = "137"
#     job_id = '3001'
#     info = parse_xxl_job(df, job_id)
#     try:
#         info = parse_xxl_job(df, xxl_job_id=str(xxl_job_id))
#     except:
#         info = {}
#     err_msg = ''
#     job_type = '同步'
#     err = f'**任务类型**: {job_type}'
#     err += f'\n\n**xxl_job_id**: {xxl_job_id}'
#     err += f'\n\n**job_id**: {job_id}'
#     if 'job_desc' in info:
#         job_desc = info['job_desc']
#         err = f'\n\n**任务名称**: {job_desc}'

#     if 'job_tracking' in info:
#         job_tracking = ' <- '.join(info['job_tracking'])
#         err += f'\n\n**任务调用链**: {job_tracking}'

#     if 'next_time' in info:
#         next_time = info['next_time']
#         err += f'\n\n**下次执行时间**: {next_time}'
#     err += f'\n\n**报错信息**: {err_msg}'

#     print(err)



def get_error_handle(err_msg):
    sql = '''
        SELECT
            id,
            error_pattern,
            action_type,
            action_params 
        FROM
            etl_error_handling_config
    '''
    rule_id, action = None, None
    try:
        import pandas as pd
        df = pd.DataFrame({'id':[1],'error_pattern':["add batch req success but status isn't ok"],'action_type':['message'],'action_params':['okk']  })
        for eid, error_pattern, action_type, action_params in df[['id', 'error_pattern', 'action_type', 'action_params']].values:
            if re.search(error_pattern, err_msg):
                if action_type == 'message':
                    rule_id = str(eid)
                    action = str(action_params)
                    break
    except:
        pass
    return rule_id, action


sss = '''
(pymysql.err.OperationalError) (1105, "errCode = 2, detailMessage = (172.16.1.105)[INTERNAL_ERROR][INTERNAL_ERROR]VNodeChannel[1771177546124-1761808442541], load_id=456728ac0d4d4cd3-8c24e94ac993107b, txn_id=14803561229090816, node=172.16.1.106:8060, add batch req success but status isn't ok, err: [INTERNAL_ERROR]PStatus: (172.16.1.106)[INTERNAL_ERROR]failed to prepare rowset: failed to save recycle rowset, err=MaybeCommitted\n\n\t0#  doris::Status doris::Status::create(doris::PStatus const&) at /usr/local/ldb-toolchain-v0.26/bin/../lib/gcc/x86_64-pc-linux-gnu/15/include/g++-v15/bits/basic_string.h:239\n\t1#  doris::vectorized::VNodeChannel::_add_block_success_callback(doris::PTabletWriterAddBlockResult const&, doris::vectorized::WriteBlockCallbackContext const&) at /home/zcp/repo_center/doris_release/doris/be/src/common/status.h:524\n\t2#  std::_Function_handler<void (doris::PTabletWriterAddBlockResult const&, doris::vectorized::WriteBlockCallbackContext const&), doris::vectorized::VNodeChannel::init(doris::RuntimeState*)::$_1>::_M_invoke(std::_Any_data const&, doris::PTabletWriterAddBlockResult const&, doris::vectorized::WriteBlockCallbackContext const&) at /usr/local/ldb-toolchain-v0.26/bin/../lib/gcc/x86_64-pc-linux-gnu/15/include/g++-v15/bits/shared_ptr_base.h:336\n\t3#  doris::vectorized::WriteBlockCallback::call() at /usr/local/ldb-toolchain-v0.26/bin/../lib/gcc/x86_64-pc-linux-gnu/15/include/g++-v15/bits/std_function.h:0\n\t4#  doris::AutoReleaseClosure<doris::PTabletWriterAddBlockRequest, doris::vectorized::WriteBlockCallback >::Run() at /usr/local/ldb-toolchain-v0.26/bin/../lib/gcc/x86_64-pc-linux-gnu/15/include/g++-v15/bits/shared_ptr_base.h:336\n\t5#  doris::FailureDetectClosure::Run() at /home/zcp/repo_center/doris_release/doris/be/src/util/brpc_client_cache.h:69\n\t6#  brpc::Controller::EndRPC(brpc::Controller::CompletionInfo const&)\n\t7#  brpc::policy::ProcessRpcResponse(brpc::InputMessageBase*)\n\t8#  brpc::ProcessInputMessage(void*)\n\t9#  brpc::InputMessenger::InputMessageClosure::~InputMessageClosure()\n\t10# brpc::InputMessenger::OnNewMessages(brpc::Socket*)\n\t11# brpc::Socket::ProcessEvent(void*)\n\t12# bthread::TaskGroup::task_runner(long)\n\t13# bthread_make_fcontext\n, host: 172.16.1.106") [SQL: insert into pos_order_goods( order_id, line_no, order_date, order_time, store_id, store_code, goods_id, member_id, cashier_id, card_no, retail_price, screen_price, member_price, discount_price, sales_qty, sales_amt, retail_sales_amt, screen_sales_amt, discount_amt, cost_amt, tax_amt, erp_time, etl_time ) select concat( b1.posno, b1.flowno ) as order_id, b2.itemno as line_no, date( b1.fildate ) as order_date, b1.fildate as order_time, w.storegid as store_id, s.code as store_code, b2.gid as goods_id, b1.memberid as member_id, b1.cashier as cashier_id, b1.cardno as card_no, b2.rtlprc as retail_price, b2.scrprice as screen_price, g.mbrprc as member_price, v.discount_price, b2.qty as sales_qty, b2.realamt as sales_amt, b2.stdtotal as retail_sales_amt, b2.scrtotal as screen_sales_amt, b2.favamt as discount_amt, b2.iamt as cost_amt, b2.itax as tax_amt, b1.rcvtime as erp_time, now() as etl_time from ods.hd_buy1s b1 join ods.hd_buy2s b2 on b2.posno = b1.posno and b2.flowno = b1.flowno join ods.hd_workstation w on w.no = b1.posno join ods.hd_store s on w.storegid = s.gid join ods.hd_goods g on b2.gid=g.gid left join dwd.promotion_goods v on b2.gid=v.goods_id where b1.rcvtime >= (select max(erp_time) from pos_order_goods where order_date >= date_sub(current_date(), interval 10 day))] (Background on this error at: https://sqlalche.me/e/20/e3q8)
'''
print(get_error_handle(sss))