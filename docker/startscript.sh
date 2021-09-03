#!/bin/bash
#set -x

PID_PY=0
PID_NR=0
# SIGTERM-handler
term_handler() {
  if [ $PID_PY -ne 0 ]; then
    kill -TERM "$PID_PY"
    wait "$PID_PY"
  fi
  if [ $PID_NR -ne 0 ]; then
    kill -TERM "$PID_NR"
    wait "$PID_NR"
  fi
  exit 143; # 128 + 15 -- SIGTERM
}

trap 'kill ${!}; term_handler' TERM

FILE=/data
if ! test -d "${FILE}"; then
    print "/data not found!"
    exit 1
fi

FILE=/data/..npm.backup
if test -d "${FILE}"; then
    rm -rf ${FILE}
     print "removed ${FILE}"
fi


FILE=/data/.node-red
if [ ! -d "${FILE}" ]
then
#    mkdir ${FILE}
    mkdir -p /data/.node-red/node_modules/pynodered
    print "created ${FILE}"
fi

FILE_NR=/usr/src/node-red/.node-red
if [ ! -d "${FILE_NR}" ]
then
    ln -fs ${FILE} ${FILE_NR}
     print "created link ${FILE_NR} --> ${FILE} "
fi


FILE=/data/requirements.txt
if test -f "${FILE}"; then
    pip3 install -r ${FILE}
fi

FILE=/data/start.py
if ! test -f "${FILE}"; then
    tee -a ${FILE} > /dev/null <<EOF

from pynodered import node_red

@node_red(category="pyfuncs")
def lower_case(node, msg):

    msg['payload'] = str(msg['payload']).lower()
    return msg
EOF

fi

# Start the first process
export PYTHONPATH=/usr/local/lib/python3.8/dist-packages/:/data/:$PYTHONPATH
echo $PYTHONPATH
echo "############ Starting pynodered"
pynodered /data/start.py &
PID_PY=$!
sleep 5
echo "############ pynodered started"


#status=$?
#if [ $status -ne 0 ]; then
#  echo "Failed to start pynodered: $status"
#  exit $status
#fi


# Start the second process
#npm --no-update-notifier --no-fund start --cache /data/.npm -- --userDir /data -D
#node-red --cache /data --userDir /data --settings /data/.node-red/settings.js 
#node-red --userDir /data/.node-red  --settings /data/.node-red/settings.js /data/.node-red/flows.json
node-red --userDir /data/.node-red /data/.node-red/flows.json &
PID_NR=$!

ps aux |grep node-red |grep -q -v grep

status=$?
if [ $status -ne 0 ]; then
  echo "Failed to start node-red: $status"
  exit $status
fi

# Naive check runs checks once a minute to see if either of the processes exited.
# This illustrates part of the heavy lifting you need to do if you want to run
# more than one service in a container. The container exits with an error
# if it detects that either of the processes has exited.
# Otherwise it loops forever, waking up every 60 seconds

while sleep 5; do
  ps aux |grep pynodered |grep -q -v grep
  PROCESS_1_STATUS=$?
  if [ $PROCESS_1_STATUS -ne 0 ]; then
    pynodered /data/start.py &
    PID_PY=$!

  fi

  ps aux |grep node-red |grep -q -v grep
  PROCESS_2_STATUS=$?
  # If the greps above find anything, they exit with 0 status
  # If they are not both 0, then something is wrong
#  if [ $PROCESS_1_STATUS -ne 0 -o $PROCESS_2_STATUS -ne 0 ]; then
   if [ $PROCESS_2_STATUS -ne 0 ]; then

    echo "NodeRed exited."
    exit $PROCESS_2_STATUS
  fi
done

