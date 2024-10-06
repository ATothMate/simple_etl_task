#!/bin/bash

# Set working directory
cd /app

# Set PYTHONPATH
export PYTHONPATH=/app/sdu_qm_task

# Execute script with logging
/usr/local/bin/python -m sdu_qm_task.feeder.feeder >> /var/log/cron.log 2>&1
