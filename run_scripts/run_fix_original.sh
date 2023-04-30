# Name args
EDGELIST_NAME=$1
GRAPHLET_SIZE=$2

source run.env
# Setup logging
LOG_OUT=$LOG_BASE/fix_original/$EDGELIST_NAME/$GRAPHLET_SIZE
mkdir -p $LOG_OUT


SCRIPT=$MA_ANALYTICS/fix_original.py

source ./pmotif_lib.env

# Run
date >> $LOG_OUT/start_time
$PYTHON_EXEC $SCRIPT \
    --edgelist_name $EDGELIST_NAME \
    --graphlet_size $GRAPHLET_SIZE \
    2> $LOG_OUT/err.log 1> $LOG_OUT/std.log
date >> $LOG_OUT/end_time
