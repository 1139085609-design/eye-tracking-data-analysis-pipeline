# -*- coding: utf-8 -*-
"""
Calcul très simple du temps entre deux AOI :
gap = début(B) - fin(A) = start_next - (start + durée)

Entrée : 20250325_0003_00_ALL_AOI_combined_in_segments.csv
Sorties :
- transition_latency_events.csv  (chaque transition)
- transition_latency_summary.csv (résumé par type de transition)
"""

import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

# ===== 1) Config batch input =====
racine_week2 = Path(r"Cours_03_ProjetRecherche_JinxuWEI/05.Recherche/AOI")
aoi_stages = ["AOI2", "AOI3", "AOI4"]

SCRIPT_DIR = Path(__file__).resolve().parent
OUT_DIR = SCRIPT_DIR

STAGE_NAME = {
    "AOI2": "Apprentice work",
    "AOI3": "Expert work",
    "AOI4": "Apprentice assist",
}


def compute_transitions_for_file(fichier_entree: Path) -> pd.DataFrame:
    df = pd.read_csv(fichier_entree)

    # Renommer les colonnes (pour simplifier)
    df = df.rename(columns={
        "AOI_Label": "aoi",
        "Start_Time(s)": "start",
        "Duration(s)": "dur"
    })

    # Vérification minimale du schéma
    required = {"aoi", "start", "dur"}
    if not required.issubset(df.columns):
        return pd.DataFrame()

    # Trier par temps (ordre chronologique)
    df = df.sort_values("start").reset_index(drop=True)

    # Calculer l'heure de fin de chaque dwell
    df["end"] = df["start"] + df["dur"]

    # COMPRESSER les répétitions consécutives d'AOI
    # On garde seulement la 1ère ligne de chaque "bloc" d'AOI identique
    df_comp = df.loc[df["aoi"].ne(df["aoi"].shift(1))].copy().reset_index(drop=True)
    df_comp["end"] = df_comp["start"] + df_comp["dur"]  # recalcul (sécurité)

    # Calculer la transition A -> B et le gap (A fin -> B début)
    df_comp["aoi_suivant"] = df_comp["aoi"].shift(-1)
    df_comp["start_suivant"] = df_comp["start"].shift(-1)
    df_comp["gap"] = df_comp["start_suivant"] - df_comp["end"]

    # On enlève la dernière ligne (pas de suivant)
    transitions = df_comp.dropna(subset=["aoi_suivant"]).copy()
    if transitions.empty:
        return transitions

    # Si gap légèrement négatif (petits recouvrements / arrondis), on met à 0
    transitions.loc[transitions["gap"] < 0, "gap"] = 0
    return transitions


all_transitions = []

for stage in aoi_stages:
    stage_dir = racine_week2 / stage
    if not stage_dir.is_dir():
        continue

    for dossier in stage_dir.iterdir():
        if not dossier.is_dir():
            continue

        fichiers = sorted(dossier.glob("*_ALL_AOI_combined_in_segments.csv"))
        for fichier_entree in fichiers:
            transitions = compute_transitions_for_file(fichier_entree)
            if transitions.empty:
                continue

            transitions["stage"] = stage
            transitions["blocking"] = dossier.name
            transitions["source_file"] = fichier_entree.name
            all_transitions.append(transitions)


def build_all_transitions() -> pd.DataFrame:
    if all_transitions:
        return pd.concat(all_transitions, ignore_index=True)
    return pd.DataFrame(
        columns=["aoi", "aoi_suivant", "end", "start_suivant", "gap", "stage", "blocking", "source_file"]
    )


def export_transition_tables(transitions_all: pd.DataFrame) -> tuple[str, str, pd.DataFrame]:
    # Export : liste des transitions (événements)
    fichier_events = str(OUT_DIR / "transition_latency_events.csv")
    transitions_all[
        ["stage", "blocking", "source_file", "aoi", "aoi_suivant", "end", "start_suivant", "gap"]
    ].to_csv(fichier_events, index=False)

    # Export : résumé par type de transition
    if transitions_all.empty:
        resume = pd.DataFrame(
            columns=["stage", "blocking", "aoi", "aoi_suivant", "n", "gap_moyen", "gap_median", "gap_ecart_type"]
        )
    else:
        resume = (
            transitions_all
            .groupby(["stage", "blocking", "aoi", "aoi_suivant"])
            .agg(
                n=("gap", "size"),
                gap_moyen=("gap", "mean"),
                gap_median=("gap", "median"),
                gap_ecart_type=("gap", "std")
            )
            .reset_index()
            .sort_values(["stage", "blocking", "n", "gap_moyen"], ascending=[True, True, False, True])
        )

    fichier_resume = str(OUT_DIR / "transition_latency_summary.csv")
    resume.to_csv(fichier_resume, index=False)
    return fichier_events, fichier_resume, resume


def export_blocking_stats_and_plot(transitions_all: pd.DataFrame) -> tuple[Path, Path]:
    if transitions_all.empty:
        marv_stats = pd.DataFrame(columns=["stage", "blocking", "mean_gap", "median_gap", "n_transitions"])
    else:
        marv_stats = (
            transitions_all
            .groupby(["stage", "blocking"], as_index=False)
            .agg(
                mean_gap=("gap", "mean"),
                median_gap=("gap", "median"),
                n_transitions=("gap", "size"),
            )
        )
        marv_stats["stage"] = marv_stats["stage"].map(STAGE_NAME).fillna(marv_stats["stage"])

    stats_path = OUT_DIR / "blocking_level_gap_stats.csv"
    marv_stats.to_csv(stats_path, index=False)

    fig_path = OUT_DIR / "boxplot_mean_gap.svg"
    plt.figure()
    if not marv_stats.empty:
        stages = marv_stats["stage"].unique()
        data = [marv_stats[marv_stats["stage"] == s]["mean_gap"] for s in stages]
        plt.boxplot(data, tick_labels=stages)

        for i, s in enumerate(stages, start=1):
            y = marv_stats[marv_stats["stage"] == s]["mean_gap"].values
            x = [i] * len(y)
            plt.scatter(x, y)

    plt.ylabel("Mean transition latency (s)")
    plt.title("Transition latency by stage (blocking level)")
    plt.savefig(fig_path)
    plt.show()
    return stats_path, fig_path


def run_pipeline() -> None:
    transitions_all = build_all_transitions()
    fichier_events, fichier_resume, _ = export_transition_tables(transitions_all)
    stats_path, fig_path = export_blocking_stats_and_plot(transitions_all)

    print(" Fichiers générés :", fichier_events, "et", fichier_resume)
    print(" Nombre de transitions calculées :", len(transitions_all))
    print(" Stats blocking enregistrées :", stats_path)
    print(" Figure enregistrée :", fig_path)


if __name__ == "__main__":
    run_pipeline()