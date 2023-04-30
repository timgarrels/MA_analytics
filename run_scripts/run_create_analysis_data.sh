# Name args
LOGS=$1
EDGELIST_NAME=$2
GRAPHLET_SIZE=$3
WORKERS=$4

mkdir -p $LOGS

source run.env

SCRIPT=$MA_ANALYTICS/create_analysis_data.py

source ./pmotif_lib.env

date >> $LOGS/start_time
$PYTHON_EXEC $SCRIPT \
    --analysis_out $OUTPUT_BASE/analysis_out \
    --edgelist_name $EDGELIST_NAME \
    --graphlet_size $GRAPHLET_SIZE \
    2> $LOGS/err.log 1> $LOGS/std.log
date >> $LOGS/end_time
