#! /bin/bash
set -x
print 'start training......'
#source /root/.bashrc
#mv /home/workspace/news /home/workspace/bak/article/news_`date -d now +%Y%m%



#!!!!!!!!!delete new news!!!!!!!######
rm -rf /home/workspace/nnews

mkdir /home/workspace/nnews
#curl 'http://127.0.0.1:19080/exportArticle?number=1000'
curl 'http://127.0.0.1:19080/exportArticle'

sleep 1

cd /home/workspace
python similarity_run.py > similarity.log

#ps -ef|grep python |grep -v grep | awk '{print $2}'|xargs kill -9

pkill -9 gunicorn
pkill -9 python


#!!!!!!!!!delete news!!!!!!!######
rm -rf /home/workspace/news
rm -rf /home/workspace/lsi
rm -rf /home/workspace/lsitemp
rm -rf /home/workspace/prefix_map

mv /home/workspace/nnews /home/workspace/news
mkdir /home/workspace/lsi
cp /home/workspace/nlsi/* /home/workspace/lsi

#python /home/workspace/service.py &

sleep 1
#python service_viva.py
#gunicorn -w4 -t 240 -k gevent -b0.0.0.0:3000 service_viva:app --preload --limit-request-line 0
gunicorn -w4 -t 600 -k gevent -b0.0.0.0:3000 service_viva:app --preload --limit-request-line 0 --worker-connections 500
