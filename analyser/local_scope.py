from scipy.stats import mannwhitneyu
import pandas as pd
import matplotlib.pyplot as plt
from statistics import quantiles

from pmotif_lib.result_transformer import ResultTransformer
from pmotif_lib.graphlet_representation import graphlet_class_to_name

from analyser.util import get_graphlet_classes


class LocalScope:
    """Creates an analysis utility object focussed on comparisons within,
    handling data loading, refining, and exposes special analysis methods"""

    def __init__(self, result: ResultTransformer):
        self.result = result

    @property
    def result_df(self):
        return self.result.positional_metric_df

    def graphlet_class_filter(self, graphlet_class: str):
        return self.result_df["graphlet_class"] == graphlet_class

    def plot_metric_distribution(self, metric_name: str):
        graphlet_classes = get_graphlet_classes(self.result_df)
        fig, axes = plt.subplots(
            1, len(graphlet_classes), figsize=(len(graphlet_classes) * 5, 5)
        )

        for i, graphlet_class in enumerate(graphlet_classes):
            ax = axes[i]
            self.result_df[self.graphlet_class_filter(graphlet_class)][
                metric_name
            ].plot.hist(
                ax=ax,
                label=metric_name,
            )
            ax.set_title(graphlet_class_to_name(graphlet_class))
            ax.legend()
        return fig

    def compute_mann_whitneyu(self, metric_name: str) -> pd.DataFrame:
        graphlet_classes = get_graphlet_classes(self.result_df)

        mannwhitneyu_results = pd.DataFrame(
            index=list(graphlet_classes),
            columns=list(graphlet_classes),
        )

        for graphlet_class_x in graphlet_classes:
            x = self.result_df[self.graphlet_class_filter(graphlet_class_x)][
                metric_name
            ]
            for graphlet_class_y in graphlet_classes:
                y = self.result_df[self.graphlet_class_filter(graphlet_class_y)][
                    metric_name
                ]
                stat = mannwhitneyu(x, y)
                mannwhitneyu_results[graphlet_class_x][graphlet_class_y] = {
                    "statistic": stat.statistic,
                    "pvalue": stat.pvalue,
                }

        rename_lookup = {
            graphlet_class: graphlet_class_to_name(graphlet_class)
            for graphlet_class in graphlet_classes
        }
        mannwhitneyu_results.rename(
            index=rename_lookup,
            columns=rename_lookup,
            inplace=True,
        )
        mannwhitneyu_results.style.set_caption("Mann-Whitney-U-test ")
        return mannwhitneyu_results

    def get_percentile_cuts(self, metric_name: str):
        graphlet_classes = get_graphlet_classes(self.result_df)

        cuts = {}
        for graphlet_class in graphlet_classes:
            metric = self.result_df[self.graphlet_class_filter(graphlet_class)][
                metric_name
            ]
            percentile_cuts = quantiles(metric, n=100, method="inclusive")

            cuts[graphlet_class] = {
                "<1%": {
                    "cut_value": round(percentile_cuts[0], 2),
                    "occurrence_count": 0,
                },
                "<5%": {
                    "cut_value": round(percentile_cuts[4], 2),
                    "occurrence_count": 0,
                },
                ">95%": {
                    "cut_value": round(percentile_cuts[-1], 2),
                    "occurrence_count": 0,
                },
                ">99%": {
                    "cut_value": round(percentile_cuts[-5], 2),
                    "occurrence_count": 0,
                },
            }

            for v in metric:
                if v < cuts[graphlet_class]["<1%"]["cut_value"]:
                    cuts[graphlet_class]["<1%"]["occurrence_count"] += 1
                if v < cuts[graphlet_class]["<5%"]["cut_value"]:
                    cuts[graphlet_class]["<5%"]["occurrence_count"] += 1
                if v > cuts[graphlet_class][">95%"]["cut_value"]:
                    cuts[graphlet_class][">95%"]["occurrence_count"] += 1
                if v > cuts[graphlet_class][">99%"]["cut_value"]:
                    cuts[graphlet_class][">99%"]["occurrence_count"] += 1
        return cuts

    def plot_occurrence_percentiles(self, metric_name: str):
        graphlet_classes = get_graphlet_classes(self.result_df)
        fig, axes = plt.subplots(
            1, len(graphlet_classes), figsize=(len(graphlet_classes) * 5, 5)
        )
        if len(graphlet_classes) == 1:
            axes = [axes]

        cuts = self.get_percentile_cuts(metric_name)

        for i, graphlet_class in enumerate(graphlet_classes):
            ax = axes[i]
            metric = self.result_df[self.graphlet_class_filter(graphlet_class)][
                metric_name
            ]

            ax.hist(metric, label=graphlet_class_to_name(graphlet_class))
            for percentile, data in cuts[graphlet_class].items():
                color = "orange" if "<" in percentile else "green"

                ax.axvline(
                    data["cut_value"],
                    label=f"{percentile} (cut={data['cut_value']}, total={data['occurrence_count']})",
                    color=color,
                    alpha=0.5,
                )

            ax.legend()
            ax.set_xlabel(metric_name)
            ax.set_ylabel("Frequency")
            ax.set_title(graphlet_class_to_name(graphlet_class))
        return fig
