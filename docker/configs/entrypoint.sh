#!/bin/bash

#Create the log directory
mkdir -p /var/log/pysiq/
touch /var/log/pysiq/pysiq.log
# chown -R www-data:www-data /var/log/pysiq/

# Read environment variables or set default values
# --  QUEUE SERVER
export SERVER_HOST_NAME="${SERVER_HOST_NAME:-0.0.0.0}"
export SERVER_PORT_NUMBER="${SERVER_PORT_NUMBER:-4444}"
export FUNCTIONS_DIRS=${FUNCTIONS_DIRS:-/shared}
export TMP_DIRECTORY=${TMP_DIRECTORY:-/tmp}
export N_WORKERS=${N_WORKERS:-2}
# --  OTHER SETTINGS
export DEBUG="${DEBUG:-False}"
export HARAKIRI="${HARAKIRI:-300}"

echo "Running entrypoint.sh for PySiQ"
echo "Environment is:"
echo "  - SERVER_HOST_NAME: ${SERVER_HOST_NAME}"
echo "  - SERVER_PORT_NUMBER: ${SERVER_PORT_NUMBER}"
echo "  - N_WORKERS: ${N_WORKERS}"
echo "  - FUNCTIONS_DIRS: ${FUNCTIONS_DIRS}"
echo "  - TMP_DIRECTORY: ${TMP_DIRECTORY}"
echo "  - DEBUG: ${DEBUG}"

#Set the shared dir permissions
# chown -R www-data:www-data $FUNCTIONS_DIRECTORY

# Check if a requirements.txt file is present for installing dependencies
if [[ -f ${FUNCTIONS_DIRECTORY}/requirements.txt ]]; then
    pip install -r ${FUNCTIONS_DIRECTORY}/requirements.txt
fi

# Launch UWSGI server
uwsgi --ini /etc/uwsgi/uwsgi.ini --enable-threads

tail -f  /var/log/pysiq/pysiq.log
