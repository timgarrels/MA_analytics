import json
from pathlib import Path
from statistics import mean, stdev
from typing import List, Dict


def get_frequency_data(p: Path) -> Dict[str, int]:
    """Load the graphlet class -> occurrence count lookup."""
    with open(p / "frequency", "r", encoding="utf-8") as frequency:
        return json.load(frequency)


def get_zscore(point: float, values: List[float]) -> float:
    """Calculate the z-score."""
    if point == 0 and set(values) == {0}:
        return 0
    return (point - mean(values)) / stdev(values)


figsize = (7,6)
dpi = 500
font_size = 22

short_metric_names = {
    "degree": "degree",
    "graph module participation ratio": "MPR",
    "min normalized anchor hop distance": "HD (min)",
    "max normalized anchor hop distance": "HD (max)",
    "mean normalized anchor hop distance": "HD (mean)",
}
