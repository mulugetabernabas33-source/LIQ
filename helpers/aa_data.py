"""
Addis Ababa Level Data Generation
Provides KPI data for all 11 Kifle Ketemas and their Weredas.
Marks range: 60-99. Top performer averages: 85-90.
All outputs deterministic via seeded RNG.
"""

# file connections / imports
import numpy as np
import pandas as pd
import streamlit as st


ADDIS_ABABA_KKS = [
    "Lideta", "Bole", "Arada", "Yeka", "Kirkos",
    "Addis Ketema", "Akaki Kaliti", "Kolfe Keranio",
    "Nifas Silk-Lafto", "Gulele", "Lemi Kura",
]

KK_WEREDAS = {
    "Lideta":           [f"Wereda {i}" for i in range(1, 11)],
    "Bole":             [f"Wereda {i}" for i in range(1, 11)],
    "Arada":            [f"Wereda {i}" for i in range(1, 9)],
    "Yeka":             [f"Wereda {i}" for i in range(1, 10)],
    "Kirkos":           [f"Wereda {i}" for i in range(1, 9)],
    "Addis Ketema":     [f"Wereda {i}" for i in range(1, 11)],
    "Akaki Kaliti":     [f"Wereda {i}" for i in range(1, 11)],
    "Kolfe Keranio":    [f"Wereda {i}" for i in range(1, 11)],
    "Nifas Silk-Lafto": [f"Wereda {i}" for i in range(1, 10)],
    "Gulele":           [f"Wereda {i}" for i in range(1, 9)],
    "Lemi Kura":        [f"Wereda {i}" for i in range(1, 8)],
}

KK_BASE_MODIFIERS = {
    "Lideta":           -0.8,
    "Bole":             +4.5,
    "Arada":            +2.1,
    "Yeka":             +0.7,
    "Kirkos":           +1.5,
    "Addis Ketema":     -3.2,
    "Akaki Kaliti":     -0.5,
    "Kolfe Keranio":    +1.2,
    "Nifas Silk-Lafto": +2.8,
    "Gulele":           -2.0,
    "Lemi Kura":        -1.5,
}

AA_SUBJECTS = [
    "Mathematics", "English", "Amharic", "Science",
    "Social Studies", "Physics", "Chemistry", "Biology",
]

_BASE_MEAN = 74.0


# seed
def _seed(name: str) -> int:
    return sum(ord(c) for c in name) * 137 + 42


# avg to pass rate
def _avg_to_pass_rate(avg: float, rng) -> float:
    """Estimate pass rate from avg score. Marks range 60-99."""
    est = (avg - 60.0) / 39.0 * 55.0 + 50.0
    return float(np.clip(est + rng.normal(0, 1.5), 50.0, 99.5))


# build kpis
def _build_kpis(avg: float, rng) -> dict:
    """Derive all KPIs from a class average and a seeded rng."""
    pass_rate       = _avg_to_pass_rate(avg, rng)
    distinction_rate = float(np.clip((avg - 70) / 25 * 50 + rng.normal(0, 2.5), 5.0, 75.0))
    at_risk          = 100.0 - pass_rate
    top_performer    = float(np.clip((avg - 70) / 25 * 40 + rng.normal(0, 2.0), 3.0, 55.0))
    improvement      = round(float(rng.uniform(0.8, 4.8)), 1)
    return {
        "overall_avg":        round(avg, 1),
        "pass_rate":          round(pass_rate, 1),
        "distinction_rate":   round(distinction_rate, 1),
        "at_risk":            round(at_risk, 1),
        "top_performer_rate": round(top_performer, 1),
        "improvement":        improvement,
    }


@st.cache_data
# get aa kpi df
def get_aa_kpi_df() -> pd.DataFrame:
    """Returns KPI DataFrame for all 11 Kifle Ketemas."""
    rows = []
    for kk in ADDIS_ABABA_KKS:
        seed = _seed(kk)
        rng  = np.random.RandomState(seed)
        mod  = KK_BASE_MODIFIERS.get(kk, 0)
        avg  = float(np.clip(_BASE_MEAN + mod + rng.normal(0, 1.2), 66, 90))
        kpis = _build_kpis(avg, rng)
        subj_scores = {}
        for j, subj in enumerate(AA_SUBJECTS):
            srng = np.random.RandomState(seed + j * 17)
            subj_scores[subj] = round(float(np.clip(avg + srng.normal(0, 2.8), 62, 93)), 1)
        rows.append({
            "Kifle Ketema": kk,
            **kpis,
            **{f"subj_{s}": v for s, v in subj_scores.items()},
        })
    return pd.DataFrame(rows)


@st.cache_data
# get aa overall kpis
def get_aa_overall_kpis() -> dict:
    """Aggregate KPIs for all of Addis Ababa."""
    df = get_aa_kpi_df()
    return {
        "overall_avg":        round(float(df["overall_avg"].mean()), 1),
        "pass_rate":          round(float(df["pass_rate"].mean()), 1),
        "distinction_rate":   round(float(df["distinction_rate"].mean()), 1),
        "at_risk":            round(float(df["at_risk"].mean()), 1),
        "top_performer_rate": round(float(df["top_performer_rate"].mean()), 1),
        "improvement":        round(float(df["improvement"].mean()), 1),
        "total_kks":          len(ADDIS_ABABA_KKS),
        "best_kk":            df.loc[df["overall_avg"].idxmax(), "Kifle Ketema"],
        "weakest_kk":         df.loc[df["overall_avg"].idxmin(), "Kifle Ketema"],
    }


@st.cache_data
# get kk summary kpis
def get_kk_summary_kpis(kk_name: str) -> dict:
    """KPI dict for a specific Kifle Ketema."""
    df  = get_aa_kpi_df()
    row = df[df["Kifle Ketema"] == kk_name]
    if row.empty:
        return {}
    r = row.iloc[0]
    return {k: r[k] for k in ["overall_avg", "pass_rate", "distinction_rate",
                                "at_risk", "top_performer_rate", "improvement"]}


@st.cache_data
# get kk subjects focus
def get_kk_subjects_focus(kk_name: str) -> list:
    """Return list of 3 weakest subjects in a KK."""
    df  = get_aa_kpi_df()
    row = df[df["Kifle Ketema"] == kk_name]
    if row.empty:
        return []
    subj_cols = [c for c in df.columns if c.startswith("subj_")]
    subj_avgs = {c.replace("subj_", ""): float(row[c].values[0]) for c in subj_cols}
    return [s for s, _ in sorted(subj_avgs.items(), key=lambda x: x[1])[:3]]


@st.cache_data
# get kk wereda df
def get_kk_wereda_df(kk_name: str) -> pd.DataFrame:
    """Per-Wereda KPI DataFrame for a specific Kifle Ketema."""
    kk_seed = _seed(kk_name)
    kk_mod  = KK_BASE_MODIFIERS.get(kk_name, 0)
    weredas = KK_WEREDAS.get(kk_name, [f"Wereda {i}" for i in range(1, 11)])
    rows = []
    for i, wereda in enumerate(weredas):
        w_seed = kk_seed + i * 997
        rng    = np.random.RandomState(w_seed)
        avg    = float(np.clip(_BASE_MEAN + kk_mod + rng.normal(0, 4), 62, 92))
        kpis   = _build_kpis(avg, rng)
        subj_scores = {}
        for j, subj in enumerate(AA_SUBJECTS):
            srng = np.random.RandomState(w_seed + j * 23)
            subj_scores[subj] = round(float(np.clip(avg + srng.normal(0, 3.5), 60, 95)), 1)
        sorted_s = sorted(subj_scores.items(), key=lambda x: x[1])
        rows.append({
            "Wereda":                 wereda,
            **kpis,
            "Subjects Needing Focus": ", ".join(s[0] for s in sorted_s[:3]),
            **{f"subj_{s}": v for s, v in subj_scores.items()},
        })
    return pd.DataFrame(rows)


@st.cache_data
# get aa heatmap df
def get_aa_heatmap_df() -> pd.DataFrame:
    """Kifle Ketema × Subject score matrix for AA-level heatmap."""
    df = get_aa_kpi_df()
    subj_cols = [c for c in df.columns if c.startswith("subj_")]
    out = df[["Kifle Ketema"] + subj_cols].copy()
    out.columns = ["Kifle Ketema"] + [c.replace("subj_", "") for c in subj_cols]
    return out


@st.cache_data
# get kk wereda heatmap df
def get_kk_wereda_heatmap_df(kk_name: str) -> pd.DataFrame:
    """Wereda × Subject score matrix for a KK-level heatmap."""
    df = get_kk_wereda_df(kk_name)
    subj_cols = [c for c in df.columns if c.startswith("subj_")]
    out = df[["Wereda"] + subj_cols].copy()
    out.columns = ["Wereda"] + [c.replace("subj_", "") for c in subj_cols]
    return out


@st.cache_data
# get aa kpi comparison df
def get_aa_kpi_comparison_df() -> pd.DataFrame:
    """KPI comparison table for all KKs (used in comparison table display)."""
    df = get_aa_kpi_df()
    return df[[
        "Kifle Ketema", "overall_avg", "pass_rate",
        "distinction_rate", "at_risk", "top_performer_rate", "improvement"
    ]].rename(columns={
        "overall_avg":        "Avg Score",
        "pass_rate":          "Pass Rate (%)",
        "distinction_rate":   "Distinction (%)",
        "at_risk":            "At-Risk (%)",
        "top_performer_rate": "Top Performer (%)",
        "improvement":        "Term Improvement (%)",
    }).sort_values("Avg Score", ascending=False).reset_index(drop=True)
