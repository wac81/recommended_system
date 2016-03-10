#! /bin/bash
set -x
print 'start training......'



#!!!!!!!!!delete new news!!!!!!!######
rm -rf /home/workspace/nnews

mkdir /home/workspace/nnews
#curl 'http://127.0.0.1:19080/exportArticle?number=1000'
curl 'http://127.0.0.1:19080/exportArticle'

sleep 1
# pkill local service:similarity_update_service
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


# remote pkill gunicorn python
ssh root@10.251.133.225  pkill -9 gunicorn
ssh root@10.251.133.225  pkill -9 python
# remote del and cp news & lsi
ssh root@10.251.133.225 rm -rf /home/workspace/news
ssh root@10.251.133.225 rm -rf /home/workspace/lsi
scp -r /home/workspace/news/ root@10.251.133.225:/home/workspace/
scp -r /home/workspace/lsi/ root@10.251.133.225:/home/workspace/
#python /home/workspace/service.py &

sleep 1
#gunicorn -w4 -t 600 -k gevent -b0.0.0.0:3000 service_viva:app --preload --limit-request-line 0 --worker-connections 500

# run getfiles
python similarity_update_service.py

# remote gunicorn
ssh root@10.251.133.225 gunicorn -w4 -t 240 -k gevent -b0.0.0.0:3000 service_viva:app --preload --limit-request-line 0

