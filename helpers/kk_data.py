# file connections / imports
import pandas as pd
import numpy as np
import streamlit as st

from .data_gen import FIRST_NAMES, LAST_NAMES
from .wereda_data import WEREDA_SCHOOLS, SCHOOL_MODIFIERS, get_subjects_for_grade, get_grade_configs

KK_SCHOOLS = list(WEREDA_SCHOOLS) + ["Yaneta", "Future", "Everest Youth Academy"]

KK_SCHOOL_MODIFIERS = dict(SCHOOL_MODIFIERS)
KK_SCHOOL_MODIFIERS.update({
    "Yaneta": 4, # High performing
    "Future": -1,
    "Everest Youth Academy": 2,
})

WEREDAS = [f"Wereda {i}" for i in range(1, 11)]

WEREDA_MODIFIERS = {
    "Wereda 1": 2,
    "Wereda 2": -1,
    "Wereda 3": 1,
    "Wereda 4": 3,
    "Wereda 5": 0,
    "Wereda 6": -2,
    "Wereda 7": 1,
    "Wereda 8": -3,
    "Wereda 9": 4,
    "Wereda 10": 0,
}


@st.cache_data
# get wereda aggregate scores
def get_wereda_aggregate_scores():
    """Returns a deterministic DataFrame of aggregated scores for all Weredas."""
    data = []

    for w in WEREDAS:
        base_mod = WEREDA_MODIFIERS[w]

        for s in KK_SCHOOLS:
            school_mod = KK_SCHOOL_MODIFIERS.get(s, 0)

            rng = np.random.RandomState(abs(hash(w + s)) % (2**31))
            noise = rng.uniform(-1.5, 1.5)

            school_avg = 75.0 + base_mod + school_mod + noise
            school_avg = min(max(school_avg, 65.0), 88.0)

            data.append({
                "Wereda": w,
                "School": s,
                "Average": round(school_avg, 2)
            })

    return pd.DataFrame(data)

# get wereda rankings
def get_wereda_rankings():
    """Get the overall average per Wereda."""
    df = get_wereda_aggregate_scores()
    ranked = df.groupby("Wereda", as_index=False)["Average"].mean()
    ranked["Average"] = ranked["Average"].round(1)
    ranked = ranked.sort_values("Average", ascending=False).reset_index(drop=True)
    return ranked

# get schools in wereda
def get_schools_in_wereda(wereda: str):
    """Get the schools and their averages in a specific Wereda."""
    df = get_wereda_aggregate_scores()
    w_df = df[df["Wereda"] == wereda].copy()
    w_df = w_df.sort_values("Average", ascending=False).reset_index(drop=True)
    return w_df


# generate kk students
def _generate_kk_students(num: int, seed: int) -> list:
    rng = np.random.RandomState(seed)
    all_names = []
    for first in FIRST_NAMES:
        for last in LAST_NAMES:
            all_names.append(f"{first} {last}")
    rng.shuffle(all_names)
    return all_names[:num]

@st.cache_data
# get kk grade data
def get_kk_grade_data(wereda: str, school: str, grade: int, track: str = None, num_students: int = 40):
    seed = abs(hash(wereda + school + str(grade) + str(track))) % (2**31)
    rng = np.random.RandomState(seed)

    students = _generate_kk_students(num_students, seed)
    subjects = get_subjects_for_grade(grade, track)

    if grade == 9:
        base_mean = 72.5
    elif grade == 10:
        base_mean = 74.5
    elif grade in [11, 12]:
        base_mean = 77.5 if track == "natural" else 75.5
    else:
        base_mean = 73.0

    w_mod = WEREDA_MODIFIERS.get(wereda, 0)
    s_mod = KK_SCHOOL_MODIFIERS.get(school, 0)
    adjusted_mean = base_mean + w_mod + s_mod

    classes = [f"{grade}A", f"{grade}B"]
    student_class_map = {s: rng.choice(classes) for s in students}

    data = []

    for cls in classes:
        cls_students = [s for s in students if student_class_map[s] == cls]
        student_competence = {}

        for student in cls_students:
            comp = rng.normal(adjusted_mean, 6.0)
            comp = min(max(comp, 60), 99)
            student_competence[student] = comp

        sorted_students = sorted(student_competence.items(), key=lambda x: x[1], reverse=True)
        top_3_names = [s[0] for s in sorted_students[:3]]

        for student in cls_students:
            comp = student_competence[student]
            is_top_3 = student in top_3_names

            for subj in subjects:
                if is_top_3:
                    mark = rng.normal(max(comp, 89.0), 3.0)
                    mark = min(max(mark, 89), 99)
                else:
                    mark = rng.normal(comp, 4.0)
                    mark = min(max(mark, 60), 99)

                data.append({
                    "Student": student,
                    "Class": cls,
                    "Subject": subj,
                    "Mark": int(round(mark))
                })

    df = pd.DataFrame(data)
    pivot_df = df.pivot_table(index=["Student", "Class"], columns="Subject", values="Mark", aggfunc='first').reset_index()
    pivot_df["Average"] = pivot_df[subjects].mean(axis=1).round(1)
    pivot_df = pivot_df.sort_values(by="Average", ascending=False).reset_index(drop=True)
    return pivot_df

# get kk prediction trend
def get_kk_prediction_trend(df: pd.DataFrame) -> str:
    """Simple helper to create a mock trend prediction."""
    if df.empty:
        return "Not enough data available for prediction."

    avg = df["Average"].mean()
    if avg > 80:
        return "Performance is consistently high. If current trend continues, expect top regional ranking."
    elif avg > 70:
        return "Performance is stable and above average. Focus on weak subjects to increase overall scores."
    else:
        return "Performance needs targeted interventions. If current trend continues, scores may stagnate."

# get class comparison
def get_class_comparison(wereda: str, school: str, grade: int, track: str = None):
    """Returns average performance of classes (e.g. 9A vs 9B)."""
    df = get_kk_grade_data(wereda, school, grade, track)
    class_avgs = df.groupby("Class", as_index=False)["Average"].mean()
    class_avgs["Average"] = class_avgs["Average"].round(1)
    return class_avgs

@st.cache_data
# get wereda grade12 analysis
def get_wereda_grade12_analysis(wereda: str, track: str):
    """Deterministically identifies best and weakest subjects for a Wereda's Grade 12 cohort."""
    rng = np.random.RandomState(abs(hash(wereda + track)) % (2**31))
    subjects = get_subjects_for_grade(12, track)

    base_mod = WEREDA_MODIFIERS.get(wereda, 0)
    scores = {}
    for subj in subjects:
        subj_modifier = 0
        if subj in ["Physics", "History", "Chemistry"]:
            subj_modifier = -4
        elif subj in ["English", "Civics"]:
            subj_modifier = 3

        score = 75.0 + base_mod + subj_modifier + rng.uniform(-3, 3)
        scores[subj] = round(min(max(score, 50), 99), 1)

    sorted_scores = sorted(scores.items(), key=lambda x: x[1])
    weakest = sorted_scores[0][0]
    strongest = sorted_scores[-1][0]

    return strongest, weakest


@st.cache_data
# get kk kpis
def get_kk_kpis() -> dict:
    """Aggregate KPIs across all Weredas in the Kifle Ketema."""
    df = get_wereda_aggregate_scores()
    all_avgs = df["Average"].tolist()
    total = len(all_avgs)

    overall_avg = round(sum(all_avgs) / total, 1) if total > 0 else 0.0
    pass_rate = round(sum(1 for a in all_avgs if a >= 66) / total * 100, 1) if total > 0 else 0.0
    distinction_rate = round(sum(1 for a in all_avgs if a >= 75) / total * 100, 1) if total > 0 else 0.0
    at_risk = round(100.0 - pass_rate, 1)
    top_performer_rate = round(sum(1 for a in all_avgs if a >= 80) / total * 100, 1) if total > 0 else 0.0

    wereda_avgs = df.groupby("Wereda")["Average"].mean().sort_values()
    weredas_needing_focus = wereda_avgs.head(3).index.tolist()

    rng = np.random.RandomState(99)
    improvement = round(float(rng.uniform(1.2, 3.8)), 1)

    return {
        "overall_avg": overall_avg,
        "pass_rate": pass_rate,
        "distinction_rate": distinction_rate,
        "at_risk": at_risk,
        "top_performer_rate": top_performer_rate,
        "improvement": improvement,
        "weredas_needing_focus": weredas_needing_focus,
    }


@st.cache_data
# get wereda kpis df
def get_wereda_kpis_df() -> "pd.DataFrame":
    """DataFrame of per-Wereda KPIs for heatmap/comparison charts."""
    import pandas as _pd
    df = get_wereda_aggregate_scores()
    rows = []
    for w in WEREDAS:
        w_df = df[df["Wereda"] == w]
        avgs = w_df["Average"].tolist()
        total = len(avgs)
        rows.append({
            "Wereda": w,
            "Avg Score": round(sum(avgs) / total, 1) if total > 0 else 0.0,
            "Pass Rate (%)": round(sum(1 for a in avgs if a >= 66) / total * 100, 1) if total > 0 else 0.0,
            "Distinction (%)": round(sum(1 for a in avgs if a >= 75) / total * 100, 1) if total > 0 else 0.0,
            "At-Risk (%)": round(sum(1 for a in avgs if a < 66) / total * 100, 1) if total > 0 else 0.0,
            "Top Performer (%)": round(sum(1 for a in avgs if a >= 80) / total * 100, 1) if total > 0 else 0.0,
        })
    return _pd.DataFrame(rows)
