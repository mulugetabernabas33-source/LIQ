"""
Wereda-level data generation module.
Generates per-school, per-grade student data for the Wereda dashboard.
"""

# file connections / imports
import pandas as pd
import numpy as np
import streamlit as st

from .data_gen import FIRST_NAMES, LAST_NAMES
from app.backend.db_functions import get_subjects


WEREDA_SCHOOLS = [
    "NEPS", "Omega", "Cruise", "Ewiket Lefire",
    "Ewiket Lehibiret", "SOS", "BGIS", "School of Tomorrow"
]

SCHOOL_MODIFIERS = {
    "NEPS": 3,
    "Omega": -2,
    "Cruise": 1,
    "Ewiket Lefire": 0,
    "Ewiket Lehibiret": -1,
    "SOS": 2,
    "BGIS": 1,
    "School of Tomorrow": 2
}


# get subjects for grade
def get_subjects_for_grade(grade: int, track: str = None) -> list:
    """
    Get the global list of subjects from the database for the Wereda dashboard data generation.
    """
    try:
        db_subjects = get_subjects()
        names = [s["name"] for s in db_subjects if s["name"] != "__TERM_ATT__"]
        if not names:
            return ["Math", "English", "Science"]
        return names
    except Exception:
        return ["Math", "English", "Science"]


# get grade configs
def get_grade_configs() -> list:
    """
    Get all grade/track configuration combinations for the Wereda dashboard.

    Returns:
        List of dicts with keys: grade (int), track (str|None), label (str)
        Contains 6 combinations: grades 9, 10, and 11/12 with natural/social tracks
    """
    return [
        {"grade": 9, "track": None, "label": "Grade 9"},
        {"grade": 10, "track": None, "label": "Grade 10"},
        {"grade": 11, "track": "natural", "label": "Grade 11 — Natural Track"},
        {"grade": 11, "track": "social", "label": "Grade 11 — Social Track"},
        {"grade": 12, "track": "natural", "label": "Grade 12 — Natural Track"},
        {"grade": 12, "track": "social", "label": "Grade 12 — Social Track"},
    ]


# generate wereda students
def _generate_wereda_students(num: int, seed: int) -> list:
    """
    Generate unique student full names for Wereda-level data.

    Uses the same Ethiopian name pools as the class-level generator,
    but with a different seed for each school/grade combination.

    Args:
        num: Number of unique students to generate
        seed: Random seed for reproducibility

    Returns:
        List of unique full names (first + last)
    """
    rng = np.random.RandomState(seed)

    all_names = []
    for first in FIRST_NAMES:
        for last in LAST_NAMES:
            all_names.append(f"{first} {last}")

    rng.shuffle(all_names)
    return all_names[:num]


# generate grade data
def generate_grade_data(school_name: str, grade: int, track: str = None, num_students: int = 40) -> pd.DataFrame:
    """
    Generate mark data for all students in a school's grade/track.

    Uses a deterministic seed based on school name, grade, and track
    for reproducibility across sessions.

    Args:
        school_name: Name of the school (e.g., "NEPS", "Omega")
        grade: Grade number (9, 10, 11, or 12)
        track: Academic track for grades 11/12 ("natural" or "social"), None for 9/10
        num_students: Number of students to generate (default: 40)

    Returns:
        DataFrame with columns: ["Student", "Subject", "Mark"]
    """
    seed = abs(hash(school_name + str(grade) + str(track))) % (2**31)
    rng = np.random.RandomState(seed)

    students = _generate_wereda_students(num_students, seed)

    subjects = get_subjects_for_grade(grade, track)

    if grade == 9:
        base_mean = 72.5
    elif grade == 10:
        base_mean = 74.5
    elif grade in [11, 12]:
        if track and track.lower() == "natural":
            base_mean = 77.5
        else:  # social
            base_mean = 75.5
    else:
        base_mean = 72.5

    school_mod = SCHOOL_MODIFIERS.get(school_name, 0)
    base_mean += school_mod

    student_competences = {}
    for student in students:
        comp = rng.normal(loc=base_mean, scale=8)
        student_competences[student] = comp

    top_3_students = sorted(students, key=lambda s: student_competences[s], reverse=True)[:3]

    records = []
    for student in students:
        is_top_3 = (student in top_3_students)
        comp = student_competences[student]

        for subject in subjects:
            if is_top_3:
                if rng.random() < 0.8: # 80% chance for exceptional mark
                    mark = rng.randint(89, 100)
                else: # 20% chance for a strong but slightly lower mark
                    mark = comp + rng.normal(loc=5, scale=4)
            else:
                mark = comp + rng.normal(loc=0, scale=6)

            mark = int(np.clip(mark, 60, 99))

            records.append({
                "Student": student,
                "Subject": subject,
                "Mark": mark
            })

    return pd.DataFrame(records)


# get wereda grade data
def get_wereda_grade_data(school_name: str, grade: int, track: str = None) -> pd.DataFrame:
    """
    Get Wereda grade data with session state caching.

    Checks st.session_state for cached data; generates and caches if not present.
    This ensures consistent data across user interactions within a session.

    Args:
        school_name: Name of the school (e.g., "NEPS", "Omega")
        grade: Grade number (9, 10, 11, or 12)
        track: Academic track for grades 11/12 ("natural" or "social"), None for 9/10

    Returns:
        DataFrame with columns: ["Student", "Subject", "Mark"]
    """
    cache_key = f"wereda_{school_name}_{grade}_{track}"

    if cache_key in st.session_state:
        return st.session_state[cache_key]

    df = generate_grade_data(school_name, grade, track)
    st.session_state[cache_key] = df

    return df

@st.cache_data
# get all wereda schools overall avg
def get_all_wereda_schools_overall_avg():
    """Computes the overall average for every school in the Wereda across all grades."""
    configs = get_grade_configs()
    data = []

    for school in WEREDA_SCHOOLS:
        total_marks = []
        for cfg in configs:
            df = generate_grade_data(school, cfg["grade"], cfg["track"])
            total_marks.extend(df["Mark"].tolist())

        avg = round(sum(total_marks) / len(total_marks), 1) if total_marks else 0.0
        data.append({"School": school, "Average": avg})

    df = pd.DataFrame(data)
    df = df.sort_values("Average", ascending=False).reset_index(drop=True)
    return df

@st.cache_data
# get wereda overall subject analysis
def get_wereda_overall_subject_analysis():
    """Aggregates all marks across the entire Wereda to find the absolute strongest and weakest subject."""
    configs = get_grade_configs()
    all_subject_marks = {}

    for school in WEREDA_SCHOOLS:
        for cfg in configs:
            df = generate_grade_data(school, cfg["grade"], cfg["track"])
            for _, row in df.iterrows():
                subj = row["Subject"]
                mark = row["Mark"]
                if subj not in all_subject_marks:
                    all_subject_marks[subj] = []
                all_subject_marks[subj].append(mark)

    subj_avgs = {}
    for subj, marks in all_subject_marks.items():
        subj_avgs[subj] = sum(marks) / len(marks)

    sorted_subjs = sorted(subj_avgs.items(), key=lambda x: x[1])
    weakest = sorted_subjs[0][0]
    strongest = sorted_subjs[-1][0]

    return strongest, weakest


@st.cache_data
# get wereda kpis
def get_wereda_kpis() -> dict:
    """
    Aggregate KPIs across all schools/grades in the Wereda.
    Returns: overall_avg, pass_rate, distinction_rate, at_risk,
             top_performer_rate, improvement, subjects_needing_focus,
             schools_needing_attention.
    """
    configs = get_grade_configs()
    all_student_avgs = []
    subject_marks = {}
    school_marks_map = {s: [] for s in WEREDA_SCHOOLS}

    for school in WEREDA_SCHOOLS:
        for cfg in configs:
            df = generate_grade_data(school, cfg["grade"], cfg["track"])
            savgs = df.groupby("Student")["Mark"].mean().tolist()
            all_student_avgs.extend(savgs)
            school_marks_map[school].extend(df["Mark"].tolist())
            for _, row in df.iterrows():
                subj = row["Subject"]
                if subj not in subject_marks:
                    subject_marks[subj] = []
                subject_marks[subj].append(int(row["Mark"]))

    total = len(all_student_avgs)
    overall_avg = round(sum(all_student_avgs) / total, 1) if total > 0 else 0.0
    pass_rate = round(sum(1 for a in all_student_avgs if a >= 60) / total * 100, 1) if total > 0 else 0.0
    distinction_rate = round(sum(1 for a in all_student_avgs if a >= 75) / total * 100, 1) if total > 0 else 0.0
    at_risk = round(100.0 - pass_rate, 1)
    top_performer_rate = round(sum(1 for a in all_student_avgs if a >= 85) / total * 100, 1) if total > 0 else 0.0

    subj_avgs = {s: sum(m) / len(m) for s, m in subject_marks.items()}
    sorted_s = sorted(subj_avgs.items(), key=lambda x: x[1])
    subjects_needing_focus = [s[0] for s in sorted_s[:3]]

    school_avg_map = {
        s: round(sum(marks) / len(marks), 1) if marks else 0.0
        for s, marks in school_marks_map.items()
    }
    schools_needing_attention = [s for s, _ in sorted(school_avg_map.items(), key=lambda x: x[1])[:2]]

    rng = np.random.RandomState(42)
    improvement = round(float(rng.uniform(1.5, 4.5)), 1)

    return {
        "overall_avg": overall_avg,
        "pass_rate": pass_rate,
        "distinction_rate": distinction_rate,
        "at_risk": at_risk,
        "top_performer_rate": top_performer_rate,
        "improvement": improvement,
        "subjects_needing_focus": subjects_needing_focus,
        "schools_needing_attention": schools_needing_attention,
    }


@st.cache_data
# get school kpis
def get_school_kpis(school_name: str) -> dict:
    """Compute KPIs for a single school across all grades."""
    configs = get_grade_configs()
    all_student_avgs = []
    subject_marks = {}

    for cfg in configs:
        df = generate_grade_data(school_name, cfg["grade"], cfg["track"])
        savgs = df.groupby("Student")["Mark"].mean().tolist()
        all_student_avgs.extend(savgs)
        for _, row in df.iterrows():
            subj = row["Subject"]
            if subj not in subject_marks:
                subject_marks[subj] = []
            subject_marks[subj].append(int(row["Mark"]))

    total = len(all_student_avgs)
    overall_avg = round(sum(all_student_avgs) / total, 1) if total > 0 else 0.0
    pass_rate = round(sum(1 for a in all_student_avgs if a >= 60) / total * 100, 1) if total > 0 else 0.0
    distinction_rate = round(sum(1 for a in all_student_avgs if a >= 75) / total * 100, 1) if total > 0 else 0.0
    at_risk = round(100.0 - pass_rate, 1)
    top_performer_rate = round(sum(1 for a in all_student_avgs if a >= 85) / total * 100, 1) if total > 0 else 0.0

    subj_avgs_map = {s: sum(m) / len(m) for s, m in subject_marks.items()}
    sorted_s = sorted(subj_avgs_map.items(), key=lambda x: x[1])
    weakest_subject = sorted_s[0][0] if sorted_s else "N/A"
    strongest_subject = sorted_s[-1][0] if sorted_s else "N/A"

    return {
        "overall_avg": overall_avg,
        "pass_rate": pass_rate,
        "distinction_rate": distinction_rate,
        "at_risk": at_risk,
        "top_performer_rate": top_performer_rate,
        "weakest_subject": weakest_subject,
        "strongest_subject": strongest_subject,
    }
