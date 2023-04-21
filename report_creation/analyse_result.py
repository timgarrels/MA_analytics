"""Generate analysis artifacts from raw analysis data."""
import argparse
import os
from pathlib import Path

import report_creation.local_analysis as local_analysis


def run_local_analysis(analysis_out, original):
    """Produce artifacts for the local (un-randomized) scope."""
    original_frequency = local_analysis.get_frequency_data(original)
    local_analysis.graphlet_pie_chart(original_frequency, analysis_out)
    local_analysis.metric_distribution(original, analysis_out)
    local_analysis.outlier_detection(original, analysis_out)


def main(analysis_out: Path, edgelist: Path, graphlet_size: int):
    analysis_data = analysis_out / edgelist.name / "raw" / str(graphlet_size)
    analysis_out = analysis_out / edgelist.name / "artifacts" / str(graphlet_size)

    local_out = analysis_out / "local"
    os.makedirs(local_out, exist_ok=True)

    original = analysis_data / edgelist.name

    run_local_analysis(local_out, original)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis_out", required=True, type=Path)
    parser.add_argument("--edgelist_path", required=True, type=Path)
    parser.add_argument("--graphlet_size", required=True, type=int, default=3, choices=[3, 4])

    args = parser.parse_args()

    main(args.analysis_out, args.edgelist_path, args.graphlet_size)
