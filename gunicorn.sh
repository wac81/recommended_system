#! /bin/bash
cd /home/workspace
gunicorn -w4 -t 600 -k gevent -b0.0.0.0:3001 service_viva:app --preload --limit-request-line 0