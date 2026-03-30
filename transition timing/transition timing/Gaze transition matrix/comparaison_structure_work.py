# -*- coding: utf-8 -*-
"""
Structural comparison:
Apprentice work (AOI2) vs Expert work (AOI3)

Inputs (from this script directory):
- transition_latency_events.csv
- transition_latency_summary.csv
- blocking_level_gap_stats.csv

Outputs (saved in this script directory):
- Transition probability matrices + heatmaps
- Entropy comparison
- Additional summaries from transition summary and blocking stats
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ====== Paths ======
SCRIPT_DIR = Path(__file__).resolve().parent
OUT_DIR = SCRIPT_DIR

EVENTS_PATH = SCRIPT_DIR / "transition_latency_events.csv"
SUMMARY_PATH = SCRIPT_DIR / "transition_latency_summary.csv"
BLOCKING_STATS_PATH = SCRIPT_DIR / "blocking_level_gap_stats.csv"


# ====== AOI category mapping ======
def mapper_aoi(label):
    text = str(label)
    if "Glass" in text:
        return "Glass"
    elif "Paper" in text:
        return "Paper"
    else:
        return "Tool"


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing input file: {path}")


# ====== Build probability matrix ======
def build_matrix(df):
    if df.empty:
        idx = ["Glass", "Paper", "Tool"]
        return pd.DataFrame(0.0, index=idx, columns=idx)
    matrice_comptage = pd.crosstab(df["from_cat"], df["to_cat"])
    # Keep a stable category order for easier cross-stage comparison
    ordered = ["Glass", "Paper", "Tool"]
    matrice_comptage = matrice_comptage.reindex(index=ordered, columns=ordered, fill_value=0)
    matrice_prob = matrice_comptage.div(matrice_comptage.sum(axis=1), axis=0)
    return matrice_prob.fillna(0)


# ====== Heatmap plotting ======
def plot_heatmap(matrix, title, output_name):
    plt.figure(figsize=(6, 5))
    plt.imshow(matrix.values)
    plt.xticks(range(len(matrix.columns)), matrix.columns)
    plt.yticks(range(len(matrix.index)), matrix.index)
    plt.colorbar()
    plt.title(title)
    plt.tight_layout()
    plt.savefig(OUT_DIR / f"{output_name}.svg")
    plt.close()


# ====== Entropy calculation ======
def compute_entropy(matrix):
    entropies = {}
    for row in matrix.index:
        probs = matrix.loc[row].values
        probs = probs[probs > 0]
        entropies[row] = -np.sum(probs * np.log2(probs))
    return entropies


def run() -> None:
    require_file(EVENTS_PATH)
    require_file(SUMMARY_PATH)
    require_file(BLOCKING_STATS_PATH)

    # 1) Load unified input files
    df_events = pd.read_csv(EVENTS_PATH)
    df_summary = pd.read_csv(SUMMARY_PATH)
    df_blocking = pd.read_csv(BLOCKING_STATS_PATH)

    # 2) Build apprentice/expert datasets from event-level table
    base = df_events.dropna(subset=["aoi", "aoi_suivant", "stage"]).copy()
    base["from_cat"] = base["aoi"].apply(mapper_aoi)
    base["to_cat"] = base["aoi_suivant"].apply(mapper_aoi)

    df_apprenti = base[base["stage"] == "AOI2"][["from_cat", "to_cat"]]
    df_expert = base[base["stage"] == "AOI3"][["from_cat", "to_cat"]]

    matrix_apprentice = build_matrix(df_apprenti)
    matrix_expert = build_matrix(df_expert)

    # 3) Save apprentice/expert matrices + heatmaps
    matrix_apprentice.to_csv(OUT_DIR / "matrix_apprentice.csv")
    matrix_expert.to_csv(OUT_DIR / "matrix_expert.csv")
    plot_heatmap(matrix_apprentice, "Apprentice Work - Transition Matrix", "heatmap_apprentice")
    plot_heatmap(matrix_expert, "Expert Work - Transition Matrix", "heatmap_expert")

    # 4) Entropy comparison
    entropy_apprentice = compute_entropy(matrix_apprentice)
    entropy_expert = compute_entropy(matrix_expert)

    df_entropy = pd.DataFrame({
        "entropy_apprentice": entropy_apprentice,
        "entropy_expert": entropy_expert
    })
    df_entropy.to_csv(OUT_DIR / "entropy_comparison.csv")

    # 5) Additional outputs using the other two input files
    # Top transition patterns from transition_latency_summary.csv
    top_summary = (
        df_summary
        .sort_values(["n", "gap_moyen"], ascending=[False, True])
        .head(30)
    )
    top_summary.to_csv(OUT_DIR / "top30_transition_patterns.csv", index=False)

    # Stage-level gap overview from blocking_level_gap_stats.csv
    stage_gap_overview = (
        df_blocking
        .groupby("stage", as_index=False)
        .agg(
            mean_of_mean_gap=("mean_gap", "mean"),
            median_of_median_gap=("median_gap", "median"),
            total_transitions=("n_transitions", "sum"),
            n_blockings=("blocking", "nunique"),
        )
        .sort_values("stage")
    )
    stage_gap_overview.to_csv(OUT_DIR / "stage_gap_overview.csv", index=False)

    print("Analysis completed. Outputs saved in:", OUT_DIR)
    print("Inputs used:")
    print(" -", EVENTS_PATH)
    print(" -", SUMMARY_PATH)
    print(" -", BLOCKING_STATS_PATH)


if __name__ == "__main__":
    run()