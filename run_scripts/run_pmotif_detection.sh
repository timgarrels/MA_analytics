# Name args
EDGELIST_NAME=$1
GRAPHLET_SIZE=$2
RANDOM_GRAPHS=$3

source run.env
# Setup logging
LOG_OUT=$LOG_BASE/pmotif_detection/$EDGELIST_NAME/$GRAPHLET_SIZE
mkdir -p $LOG_OUT


SCRIPT=$MA_ANALYTICS/pmotif_detection.py

source ./pmotif_lib.env

# Run
date >> $LOG_OUT/start_time
$PYTHON_EXEC $SCRIPT \
    --edgelist_name $EDGELIST_NAME \
    --graphlet_size $GRAPHLET_SIZE \
    --random_graphs $RANDOM_GRAPHS \
    2> $LOG_OUT/err.log 1> $LOG_OUT/std.log
date >> $LOG_OUT/end_time
