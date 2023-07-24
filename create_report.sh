echo $0
DATASET=$1
GRAPHLET_SIZE=$2

cd /home/timgarrels/masterthesis/MA_analytics
source .venv/bin/activate

python3 -m report_creation.analyse_result --analysis_out /home/timgarrels/masterthesis/prelim_analysis/_analysis_out --edgelist_name $DATASET --graphlet_size $GRAPHLET_SIZE

