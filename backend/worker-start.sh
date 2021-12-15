#! /usr/bin/env bash
set -e

python /app/app/celeryworker_pre_start.py

mkdir -p /var/run/celery /var/log/celery
chown -R nobody:nogroup /var/run/celery /var/log/celery


celery -A app.worker worker -l info --logfile=/var/log/celery/worker.log \
            -Q main-queue -c 2 --uid=nobody --gid=nogroup
