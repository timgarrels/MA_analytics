# Name args
LOGS=$1
EDGELIST_NAME=$2
GRAPHLET_SIZE=$3

mkdir -p $LOGS

source run.env

cd $MA_ANALYTICS

date >> $LOGS/start_time
$PYTHON_EXEC -m report_creation.analyse_result \
    --analysis_out $OUTPUT_BASE/analysis_out \
    --edgelist_name $EDGELIST_NAME \
    --graphlet_size $GRAPHLET_SIZE \
    2> $LOGS/err.log 1> $LOGS/std.log
date >> $LOGS/end_time
