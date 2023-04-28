# Pmotif Analytics

The scripts for the gathering and analysis of pmotif data. Based on `pmotif_lib`.

## Setup
Install the python dependencies:
```bash
pip install -r requirements
```

The `pmotif_lib` dependencies requires a [gTrieScanner executable](https://www.dcc.fc.up.pt/gtries) to work.
Download the sources, compile them, and add the executable to your path.

Furthermore, `pmotif_lib` expects certain environment vars to be set. It is recommended to create a `pmotif_lib.env` file, which can be used to export those variables:
```bash
export DATASET_DIRECTORY=/path/where/edgelists/are/located
export EXPERIMENT_OUT=/path/where/raw/graphlets/and/pmetric/should/go
export GTRIESCANNER_EXECUTABLE=/path/to/the/gtriescanner/executable
export WORKERS=1
```

## Usage

### Pmotif Detection
To run a pmotif detection pipeline, run the `pmotif_detection.py` script:
```bash
source pmotif_lib.env  # Export the env vars required by pmotif_lib
python3 pmotif_detection.py --edgelist_name your_edgelist --graphlet_size [3,4] --random_graphs [-1, n]
```
- `--edgelist_name` specifies the location of a graph edgeslist, relative to `DATASET_DIRECTORY`.
- `--graphlet_size` specifies the graphlet size, and is limited to either 3, or 4.
- `--random_graphs` specifies the number of random graphs to generate.
  - If set to a number `>= 0`, it will generate as many random graphs, and will fail if random graphs are already present.
  - If set to `-1`, it will not generate new random graphs, but reuse random graphs which are already present. Use this if you already ran with a different graphlet size and want to use the same random graphs.
Example:
```bash
source pmotif_lib.env  # Export the env vars required by pmotif_lib
python3 pmotif_detection.py --edgelist_name karate_club.edgelist --graphlet_size 3 --random_graphs 10
```
This will create a new directory in `EXPERIMENT_OUT`, named after the edgelist. It will contain the graphlets and pmetrics of the original graphs,
the random graphs, as well as the graphlets and pmetrics for each of the random graphs.

The `pmotif_detection_benchmark.py` is essentially the same script with 3 differences:
1. It removes the output after it ran
2. It creates a log file with runtimes for sub-steps of the pmotif detection pipeline
3. It takes the additional argument `--benchmarking_run`, specifying a number prefixed to the aforementioned log file

### Analysis Data Creation
Requires the output of [Pmotif Detection](#pmotif-detection) to run!

To create raw analysis data from pmotif data, run the `create_analysis_data.py` script:
```bash
source pmotif_lib.env  # Export the env vars required by pmotif_lib
python3 create_analysis_data.py --analysis_out outpath --edgelist_name your_edgelist --graphlet_size [3,4]
```
This script expects the same env vars as `pmotif_detection.py`, make sure not to change the variables or the location on disk!

- `--edgelist_name` and `--graphlet_size` have the same function as with `pmotif_detection.py`, and are used to identify the correct pmotif data to process.
- `--analysis_out` specifies the output path of the analysis data.
Example:
```bash
source pmotif_lib.env  # Export the env vars required by pmotif_lib
python3 create_analysis_data.py --analysis_out ./out --edgelist_name karate_club.edgelist --graphlet_size 3 --random_graphs 10
```
### Analysis Report Creation
Requires the output of [Analysis Data Creation](#analysis-data-creation) to run!

Finally, this script transforms the analysis data into a html analysis report. As it is independent of the `pmotif_lib`,
you do not need the env vars anymore.

```bash
python3 -m report_creation.analyse_result --analysis_out path/to/analysis/data --edgelist_name your_edgelist --graphlet_size [3,4]
```
- `--edgelist_name` and `--graphlet_size` have the same function as with `create_analysis_data.py`, and are used to identify the correct analysis data to process.
- `--analysis_out` specifies the location of the analysis data (same as in `create_analysis_data.py`) and also serves as output path for this script.
Example:
```bash
python3 -m report_creation.analyse_result --analysis_out ./out --edgelist_name karate_club.edgelist --graphlet_size 3
```
## Other
- `dataset/`  Placeholder for datasets
- `out/`  Placeholder for script output
- `run_scripts/`  Bash scripts wrappers with logging to run the python scripts on a cluster
- `slurm_helper/`  Generators of slurm batch files to run batch jobs
- `conversion/`  Utility to transform old `pmotif_lib` data format into new format
- `notebooks/`  Notebooks for prototyping
