cd /hpi/fs00/home/tim.garrels/masterthesis/motif_position_tooling/
mkdir -p $1
date >> $1/start_time
/hpi/fs00/home/tim.garrels/masterthesis/motif_position_tooling/.venv/bin/python3 -m pmotif_detection.main --edgelist_name $2 --graphlet_size $3 --benchmarking_run $4 2> $1/err.log 1> $1/std.log
date >> $1/end_time