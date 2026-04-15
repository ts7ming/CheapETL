from pyqueen import DataSource, TimeKit
from settings import DATABASES
import logging

logging.basicConfig(level=logging.INFO)


ds_erp = DataSource(**DATABASES['1001'])
ds_erp.set_db('oms')

ds_dw = DataSource(**DATABASES['1002'])
ds_dw.set_db('ods')

tk = TimeKit()

start_date = tk.yesterday10
end_date1 = tk.today10

q_sql = f'''
    select 
    from t_order
    where create_time>='{start_date}'
    and create_time<'{end_date1}'
'''

logging.info(f'读取 {start_date} 至 {end_date1} 源数据')
df = ds_erp.read_sql(q_sql)


d_sql = f'''
    delete 
    from ods_t_order 
    where create_time>='{start_date}' 
    and create_time<'{end_date1}'
'''
logging.info('删除待写入数据')
ds_dw.exe_sql(d_sql)

logging.info('写入数仓')
ds_dw.to_db(df, 'ods_t_order')