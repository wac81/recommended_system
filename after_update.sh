#! /bin/bash
set -x
echo 'start updating......'

A="root@10.251.133.225"

cd /home/workspace/
python similarity_update.py > update.log

sleep 1
# pkill local service:similarity_update_service
pkill -9 gunicorn
pkill -9 python
sleep 1

#!!!!!!!!!delete news!!!!!!!######
#rm -rf /home/workspace/lsi/viva.index
#rm -rf /home/workspace/lsi/viva.index.*
#rm -rf /home/workspace/lsi/viva.lsi
#rm -rf /home/workspace/lsi/viva.lsi.projection
#rm -rf /home/workspace/lsi/viva.mm
#rm -rf /home/workspace/lsi/viva_temp.mm
#rm -rf /home/workspace/lsi/viva_temp.mm.index
#
#
#cp /home/workspace/lsitemp/* /home/workspace/lsi/
# A machine
# copy lsi model to all machines
# remote pkill gunicorn python
ssh ${A} "pkill -9 gunicorn"
ssh ${A} "pkill -9 python"

# remote  cp added news & cp lsi
scp -r /home/workspace/news_post_add/* ${A}:/home/workspace/news/
ssh ${A} "rm -rf /home/workspace/lsi"
scp -r /home/workspace/lsi/ ${A}:/home/workspace/


# cp file map
ssh ${A} "rm -rf /home/workspace/prefix_map/"
scp -r /home/workspace/prefix_map/ ${A}:/home/workspace/


# run getfiles
nohup python similarity_update_service.py > update_service.log &

# run remote similar find
sleep 1
#gunicorn -w4 -t 240 -k gevent -b0.0.0.0:3000 service_viva:app --preload --limit-request-line 0
ssh ${A} "sh /home/workspace/gunicorn.sh"



