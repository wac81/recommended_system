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
# pkill local service:similarity_update_service
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


cp /home/workspace/lsitemp/* /home/workspace/lsi/
# A machine
# copy lsi model to all machines
# remote pkill gunicorn python
ssh root@10.251.133.225  "pkill -9 gunicorn"
ssh root@10.251.133.225  "pkill -9 python"

# remote  cp added news & cp lsi
#ssh root@10.251.133.225 "rm -rf /home/workspace/news"
ssh root@10.251.133.225 "rm -rf /home/workspace/lsi"
ssh root@10.251.133.225 "rm -rf /home/workspace/nlsi"
scp -r /home/workspace/news_post_add/ root@10.251.133.225:/home/workspace/news/
scp -r /home/workspace/lsi/ root@10.251.133.225:/home/workspace/
scp -r /home/workspace/nlsi/ root@10.251.133.225:/home/workspace/

# cp file map
ssh root@10.251.133.225 rm -rf /home/workspace/prefix_map/
scp -r /home/workspace/prefix_map/ root@10.251.133.225:/home/workspace/
# B machine
#scp /home/workspace/lsitemp/* root@10.144.141.135:/home/workspace/lsi

# run getfiles
nohup python similarity_update_service.py > service.log &

# run remote similar find
sleep 1
#gunicorn -w4 -t 240 -k gevent -b0.0.0.0:3000 service_viva:app --preload --limit-request-line 0
ssh root@10.251.133.225 "sh /home/workspace/gunicorn.sh"



