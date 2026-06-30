#!/bin/bash

# Define the cleanup function
cleanup() {
    echo "One of the nodes has stopped! Terminating all remaining processes..."
    # Hide both stdout and stderr errors during force-kill
    kill $PID1 $PIDR1 $PID2 $PID3 $PID4 2>/dev/null
    exit 1
}

# Launch all nodes strictly in the background using '&'
python3 imu.py &
PID1=$!

sleep 1
ros2 run joy joy_node &
PIDR1=$!

sleep 2
python3 joynode.py &
PID2=$!

sleep 3
python3 moter_value_converter.py &
PID3=$!

sleep 4
python3 motor.py &  
PID4=$!

echo "All nodes successfully launched. Monitoring system..."


wait -n

# The moment one process dies, the script drops down here and triggers cleanup
cleanup
