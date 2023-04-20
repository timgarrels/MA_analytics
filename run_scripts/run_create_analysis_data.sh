# Name user input
LOG_DIR=$1
mkdir -p $LOG_DIR
EDGELIST_NAME=$2
GRAPHLET_SIZE=$3

# Setup env for pmotif_lib
export DATASET_DIRECTORY=/hpi/fs00/home/tim.garrels/masterthesis/datasets
export EXPERIMENT_OUT=/hpi/fs00/home/tim.garrels/masterthesis/output/data_collection_out
export GTRIESCANNER_EXECUTABLE=/hpi/fs00/home/tim.garrels/masterthesis/bin/gtrieScanner/gtrieScanner

# Name create_analysis_data.py args
ANAYLSIS_OUT=/hpi/fs00/home/tim.garrels/masterthesis/output/analysis_out
EDGELIST_PATH=$DATASET_DIRECTORY/$EDGELIST_NAME

# Navigate to code repo
REPO_PATH=/hpi/fs00/home/tim.garrels/masterthesis/MA_analytics
cd $REPO_PATH

$REPO_PATH/.venv/bin/python3 create_analysis_data.py \
  --analysis_out $ANAYLSIS_OUT \
  --edgelist_path $EDGELIST_PATH \
  --graphlet_size $GRAPHLET_SIZE \
  --graphlet_data $EXPERIMENT_OUT \
  2> $LOG_DIR/err.log 1> $LOG_DIR/std.log
