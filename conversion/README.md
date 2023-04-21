Due to polishment of the `pmotif_lib` the on disk format changed when moving to version `1.0.0`.

The old format is not readable anymore by the current `pmotif_lib` version, but theoretically compatible.

We already computed results with an old `pmotif_lib` version.
As that previous computation took a lot of time, we want to convert the old result to be readable again by version `1.0.0`

- The utility `converter.py` can translate old results into the new.
- The utility `assert_result_equality.py` can test whether two new results are equal
- The script `test_conversion.sh` first runs a conversion, and then tests whether the conversion
    result is the same as a newly computed result.