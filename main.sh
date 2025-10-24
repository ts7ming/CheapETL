## crontab环境变量
export LD_LIBRARY_PATH=/opt/oracle-tools/instantclient_11_2:$LD_LIBRARY_PATH
export PATH=$PATH:/opt/oracle-tools/instantclient_11_2

cd ~/CheapETL;

if [ $# -eq 0 ]; then
    python3 main.py
else
    python3 main.py $1
fi


