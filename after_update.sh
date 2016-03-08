#! /bin/bash
set -x
print 'start training......'
#source /root/.bashrc
#mv /home/workspace/news /home/workspace/bak/article/news_`date -d now +%Y%m%

# workspace = baobao/Documents/LSI-for-ChineseDocument


#ps -ef|grep python |grep -v grep | awk '{print $2}'|xargs kill -9

cd /home/workspace/
python similarity_update.py > update.log
sleep 1

pkill -9 gunicorn
pkill -9 python

sleep 1

#!!!!!!!!!delete news!!!!!!!######
rm -rf /home/workspace/lsi/viva.index
rm -rf /home/workspace/lsi/viva.index.*
rm -rf /home/workspace/lsi/viva.lsi
rm -rf /home/workspace/lsi/viva.lsi.projection
rm -rf /home/workspace/lsi/viva.mm
rm -rf /home/workspace/lsi/viva_temp.mm
rm -rf /home/workspace/lsi/viva_temp.mm.index

# copy lsi model to all machines
cp /home/workspace/lsitemp/* /home/workspace/lsi/

# A machine
scp /home/workspace/lsitemp/* root@10.144.141.134:/home/workspace/lsi

# B machine
#scp /home/workspace/lsitemp/* root@10.144.141.135:/home/workspace/lsi


cd /home/workspace/
sleep 1
#gunicorn -w4 -t 240 -k gevent -b0.0.0.0:3000 service_viva:app --preload --limit-request-line 0
gunicorn -w4 -t 6000 -k gevent -b0.0.0.0:3000 service_viva:app --preload --limit-request-line 0 --worker-connections 500



