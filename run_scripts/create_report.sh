# Name args
EDGELIST_NAME=$1
GRAPHLET_SIZE=$2


source run.env
# Setup logging
LOG_OUT=$LOG_BASE/create_report/$EDGELIST_NAME/$GRAPHLET_SIZE
mkdir -p $LOG_OUT

cd $MA_ANALYTICS

# Run
date >> $LOG_OUT/start_time
$PYTHON_EXEC -m report_creation.analyse_result \
    --analysis_out $OUT_BASE/analysis_out \
    --edgelist_name $EDGELIST_NAME \
    --graphlet_size $GRAPHLET_SIZE \
    2> $LOG_OUT/err.log 1> $LOG_OUT/std.log
date >> $LOG_OUT/end_time
