#! /bin/bash
set -x
echo 'start updating......'

A=("10.251.133.225" "10.163.108.8")

cd /home/workspace/
python similarity_update.pyc > update.log

sleep 1
# pkill local service:similarity_update_service
#pkill -9 gunicorn
#pkill -9 python
sleep 1

#nohup gunicorn -w1 -t 600 -k gevent -b0.0.0.0:3001 service_viva:app --preload --limit-request-line 0 &

# A machine
# copy lsi model to all machines
# remote pkill gunicorn python
for client in ${A[@]}; do

ssh $client "sh /home/workspace/stop_service.sh"

# remote  cp added news & cp lsi
scp -r /home/workspace/news_post_add/* $client:/home/workspace/news/
ssh $client "rm -rf /home/workspace/lsi"
scp -r /home/workspace/lsi/ $client:/home/workspace/


# cp file map
ssh $client "rm -rf /home/workspace/prefix_map/"
scp -r /home/workspace/prefix_map/ $client:/home/workspace/

#gunicorn -w4 -t 600 -k gevent -b0.0.0.0:3000 service_viva:app --preload --limit-request-line 0
ssh $client "sh /home/workspace/gunicorn.sh"
sleep 2

done

# run getfiles
#nohup python similarity_update_service.pyc > update_service.log &

# run remote similar find
sleep 15
exit

