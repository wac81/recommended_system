#! /bin/bash
set -x
echo 'start training......'

A="root@10.251.133.225"

#!!!!!!!!!delete new news!!!!!!!######
rm -rf /home/workspace/nnews
rm -rf /home/workspace/nlsi

mkdir /home/workspace/nnews
#curl 'http://127.0.0.1:19080/exportArticle?number=2000'
curl 'http://127.0.0.1:19080/exportArticle'

sleep 1
# pkill local service:similarity_update_service
pkill -9 gunicorn
pkill -9 python
sleep 1

cd /home/workspace
python similarity_run.py > similarity.log

#ps -ef|grep python |grep -v grep | awk '{print $2}'|xargs kill -9


#!!!!!!!!!delete news!!!!!!!######
rm -rf /home/workspace/news
rm -rf /home/workspace/lsi
rm -rf /home/workspace/lsitemp
rm -rf /home/workspace/prefix_map

mv /home/workspace/nnews /home/workspace/news
mkdir /home/workspace/lsi
cp /home/workspace/nlsi/* /home/workspace/lsi

nohup gunicorn -w1 -t 600 -k gevent -b0.0.0.0:3001 service_viva:app --preload --limit-request-line 0 > service.log &

# remote pkill gunicorn python
ssh ${A}  "pkill -9 gunicorn"
ssh ${A}  "pkill -9 python"
# remote del and cp news & lsi
ssh ${A} "rm -rf /home/workspace/news"
ssh ${A} "rm -rf /home/workspace/lsi"
ssh ${A} "rm -rf /home/workspace/nlsi"
scp -r /home/workspace/news/ ${A}:/home/workspace/
scp -r /home/workspace/lsi/ ${A}:/home/workspace/
scp -r /home/workspace/nlsi/ ${A}:/home/workspace/
#python /home/workspace/service.py &

sleep 1
#gunicorn -w4 -t 600 -k gevent -b0.0.0.0:3000 service_viva:app --preload --limit-request-line 0 --worker-connections 500

# run getfiles
nohup python similarity_update_service.py > update_service.log &

sleep 1
# remote gunicorn
# run remote similar find
#ssh ${A} "gunicorn -w4 -t 240 -k gevent -b0.0.0.0:3000 service_viva:app --preload --limit-request-line 0"
ssh ${A} "sh /home/workspace/gunicorn.sh"
exit

