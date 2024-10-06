#!/bin/bash

# Set environment variables
source /etc/environment

# Set working directory
cd /app

# Set PYTHONPATH
export PYTHONPATH=/app/sdu_qm_task

# Execute script with logging
/usr/local/bin/python -m sdu_qm_task.etl.pre_loader >> /var/log/cron.log 2>&1
