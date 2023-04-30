# Name args
EDGELIST_NAME=$1
GRAPHLET_SIZE=$2
USER_WORKERS=$3

source run.env
# Setup logging
LOG_OUT=$LOG_BASE/create_analysis_data/$EDGELIST_NAME/$GRAPHLET_SIZE
mkdir -p $LOG_OUT

SCRIPT=$MA_ANALYTICS/create_analysis_data.py

source ./pmotif_lib.env
WORKERS=$USER_WORKERS  # Overwrite WORKERS taken from pmotif_lib

# Run
date >> $LOG_OUT/start_time
$PYTHON_EXEC $SCRIPT \
    --analysis_out $EXPERIMENT_OUT/analysis_out \
    --edgelist_name $EDGELIST_NAME \
    --graphlet_size $GRAPHLET_SIZE \
    2> $LOG_OUT/err.log 1> $LOG_OUT/std.log
date >> $LOG_OUT/end_time
