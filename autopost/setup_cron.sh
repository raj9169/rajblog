#!/bin/bash
# Setup cron jobs for auto-posting at 6 AM and 6 PM IST
# IST = UTC + 5:30, so 6 AM IST = 0:30 UTC, 6 PM IST = 12:30 UTC

SCRIPT_DIR="/home/ubuntu/rajblog"
VENV_PATH="$SCRIPT_DIR/venv/bin/python"
RUN_SCRIPT="$SCRIPT_DIR/autopost/run.py"
LOG_FILE="$SCRIPT_DIR/autopost/autopost.log"

# Load environment variables from .env
ENV_FILE="$SCRIPT_DIR/.env"

# Create the cron command
CRON_CMD="cd $SCRIPT_DIR && export \$(grep -v '^#' $ENV_FILE | xargs) && $VENV_PATH $RUN_SCRIPT >> $LOG_FILE 2>&1"

# Remove existing autopost cron jobs
crontab -l 2>/dev/null | grep -v "autopost/run.py" | crontab -

# Add new cron jobs (6 AM IST = 0:30 UTC, 6 PM IST = 12:30 UTC)
(crontab -l 2>/dev/null; echo "30 0 * * * $CRON_CMD") | crontab -
(crontab -l 2>/dev/null; echo "30 12 * * * $CRON_CMD") | crontab -

echo "Cron jobs set up successfully:"
echo "  - 6:00 AM IST (0:30 UTC) daily"
echo "  - 6:00 PM IST (12:30 UTC) daily"
echo ""
echo "Log file: $LOG_FILE"
echo ""
echo "To verify: crontab -l"
echo "To test manually: cd $SCRIPT_DIR && source venv/bin/activate && python autopost/run.py"
