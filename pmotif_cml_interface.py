import argparse
from pathlib import Path


def add_common_args(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--edgelist-path",
        required=True,
        type=Path,
        help="Path to the edgelist you want to compute on. Has to be in format `u v` or `u v w`, where "
             "`u` and `v` are node IDs above 0 and `w` is a weight (which will be ignored by gTrieScanner)",
    )
    parser.add_argument(
        "--graphlet-size",
        required=True,
        type=int,
        default=3,
        choices=[3, 4],
        help="The size of subgraphs to iterate and test for isomorphism classes. Every increment of this substantially "
             "increases the runtime! Therefore, options are limited to only 3 and 4.",
    )


def add_experiment_out_arg(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--experiment-out",
        required=True,
        type=Path,
        help="Path where graphlets and pMetric results of original graph and potential random graphs will be saved.",
    )


def add_analysis_out_arg(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--analysis-out",
        required=True,
        type=Path,
        help="Path where analysis data such as consolidated metrics and report artifacts will be saved.",
    )


def add_workers_arg(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--workers",
        required=True,
        type=int,
        default=1,
        help="Degree of Parallelization for certain processes.",
    )
