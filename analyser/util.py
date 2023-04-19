import pandas as pd
from pandas import DataFrame
from statistics import mean, stdev
from typing import List, Set, Dict

from pmotif_lib.graphlet_representation import (
    get_graphlet_size_from_class,
    graphlet_classes_from_size,
)
from pmotif_lib.p_metric.metric_consolidation import metrics
from pmotif_lib.result_transformer import ResultTransformer


def add_consolidated_metrics(result: ResultTransformer) -> ResultTransformer:
    for metric_name, consolidation_metric_list in metrics.items():
        for consolidation_name, consolidation_method in consolidation_metric_list:
            result.consolidate_metric(
                metric_name, consolidation_name, consolidation_method
            )
    return result


def get_graphlet_classes(result_df: DataFrame) -> Set[str]:
    """Extracts the graphlet classes present in a result dataframe"""
    return set(result_df["graphlet_class"])


def to_graphlet_class_frequency(result_df: pd.DataFrame) -> Dict[str, int]:
    graphlet_size = get_graphlet_size_from_class(result_df["graphlet_class"][0])
    all_frequencies = dict.fromkeys(graphlet_classes_from_size(graphlet_size), 0)

    return {
        **all_frequencies,
        **dict(result_df.groupby("graphlet_class").agg("count")["nodes"]),
    }


def get_zscore(point: float, values: List[float]) -> float:
    if point == 0 and set(values) == {0}:
        return 0
    return (point - mean(values)) / stdev(values)


def extract_metric_distribution(df, metric_name):
    return dict(df.groupby("graphlet_class").agg(list)[metric_name])
