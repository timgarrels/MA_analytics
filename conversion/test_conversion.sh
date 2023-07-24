# Run result conversion against old format, and test equality of the converted result against a result computed
# in the new format!

source ../.venv/bin/activate
python3 converter.py --target_path test_artifacts/old_format/kaggle_star_wars.edgelist_motifs/3/positional_data

python3 assert_result_equality.py \
--edgelist-path ./test_artifacts/datasets/kaggle_star_wars.edgelist \
--graphlet_size 3 \
--first_result ./test_artifacts/old_format \
--second_result ./test_artifacts/new_format

# Clean up conversion
rm -rf test_artifacts/old_format/kaggle_star_wars.edgelist_motifs/3/pmetrics
