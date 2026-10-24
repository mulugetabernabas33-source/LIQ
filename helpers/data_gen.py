"""
Data generation module for student marks and class data.
Provides functions to generate deterministic, reproducible student data.
"""

# file connections / imports
import pandas as pd
import numpy as np
import streamlit as st


from app.backend.db_functions import get_subjects

FIRST_NAMES = [
    "Kebede", "Abebe", "Jallel", "Bernabas", "Barkot", "Abdellah", "Nathan",
    "Yared", "Mulugeta", "Daniel", "Million", "Dawit", "Hanna", "Selam",
    "Tigist", "Frehiwot", "Biruk", "Kalkidan", "Ermias", "Solomon", "Mikael",
    "Amanuel", "Henok", "Kidist", "Betlehem", "Rahel", "Sara", "Abel",
    "Nahom", "Tewodros"
]

LAST_NAMES = [
    "Tadesse", "Bekele", "Haile", "Tesfaye", "Girma", "Assefa", "Mekonnen",
    "Worku", "Alemayehu", "Fikadu", "Negash", "Wolde", "Gebre", "Desta",
    "Shiferaw", "Zewde", "Kebede", "Alemu", "Bogale", "Lemma"
]

ALL_CLASSES = [
    "9A", "9B", "9C", "9D",
    "10A", "10B", "10C", "10D",
    "11A", "11B", "11C", "11D",
    "12A", "12B", "12C", "12D"
]


# get subjects for class
def get_subjects_for_class(class_name: str) -> list:
    """
    Get the global list of subjects from the database.
    """
    try:
        db_subjects = get_subjects()
        names = [s["name"] for s in db_subjects if s["name"] != "__TERM_ATT__"]
        if not names:
            # Fallback if db is completely empty
            return ["Math", "English", "Science"]
        return names
    except Exception:
        return ["Math", "English", "Science"]


# get track label
def get_track_label(class_name: str) -> str:
    """
    Get the academic track label for a class.

    Args:
        class_name: Class identifier (e.g., "11A", "12C")

    Returns:
        Track label string or empty string for grades 9/10
    """
    grade = int(class_name[:-1])
    section = class_name[-1].upper()

    if grade in [9, 10]:
        return ""

    if section in ["A", "B"]:
        return "Natural Track"

    return "Social Track"


# get all classes for grade
def get_all_classes_for_grade(grade: int) -> list:
    """
    Get all class sections for a given grade.

    Args:
        grade: Grade number (9, 10, 11, or 12)

    Returns:
        List of class names (e.g., ["9A", "9B", "9C", "9D"])
    """
    return [f"{grade}A", f"{grade}B", f"{grade}C", f"{grade}D"]


# generate students
def _generate_students(num: int, seed: int) -> list:
    """
    Generate unique student full names.

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


# generate class data
def generate_class_data(class_name: str, num_students: int = 30) -> pd.DataFrame:
    """
    Generate mark data for all students in a class.

    Uses a deterministic seed based on class name for reproducibility.

    Args:
        class_name: Class identifier (e.g., "11A")
        num_students: Number of students to generate (default: 30)

    Returns:
        DataFrame with columns: ["Student", "Subject", "Mark"]
    """
    seed = sum(ord(c) for c in class_name) * 100
    rng = np.random.RandomState(seed)

    students = _generate_students(num_students, seed)

    subjects = get_subjects_for_class(class_name)

    import re
    match = re.match(r"(\d+)([A-Za-z])", class_name)
    if match:
        grade = int(match.group(1))
        section = match.group(2).upper()
    else:
        grade = 9
        section = "A"

    track_label = get_track_label(class_name)

    if grade == 9:
        base_mean = 72.5
    elif grade == 10:
        base_mean = 74.5
    elif grade in [11, 12]:
        if "natural" in track_label.lower():
            base_mean = 77.5
        else:  # social
            base_mean = 75.5
    else:
        base_mean = 72.5

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


# get class data
def get_class_data(class_name: str) -> pd.DataFrame:
    """
    Get class data with session state caching.

    Checks st.session_state for cached data; generates and caches if not present.

    Args:
        class_name: Class identifier (e.g., "11A")

    Returns:
        DataFrame with columns: ["Student", "Subject", "Mark"]
    """
    cache_key = f"data_{class_name}"

    if cache_key in st.session_state:
        return st.session_state[cache_key]

    df = generate_class_data(class_name)
    st.session_state[cache_key] = df

    return df


# generate class data by term
def generate_class_data_by_term(class_name: str, term_index: int = 0, num_students: int = 30) -> pd.DataFrame:
    """
    Generate mark data for a specific term (term_index 0=Q1 … 3=Q4).
    Uses a prime-offset seed per term so Q2 slightly improves on Q1.
    """
    import re
    base_seed = sum(ord(c) for c in class_name) * 100
    seed = (base_seed + term_index * 7919) % (2 ** 31)
    rng = np.random.RandomState(seed)

    students = _generate_students(num_students, seed)
    subjects = get_subjects_for_class(class_name)

    match = re.match(r"(\d+)([A-Za-z])", class_name)
    grade = int(match.group(1)) if match else 9
    track_label = get_track_label(class_name)

    if grade == 9:
        base_mean = 72.5
    elif grade == 10:
        base_mean = 74.5
    elif grade in [11, 12]:
        base_mean = 77.5 if "natural" in track_label.lower() else 75.5
    else:
        base_mean = 72.5

    base_mean += term_index * 0.6

    student_competences = {}
    for student in students:
        comp = rng.normal(loc=base_mean, scale=8)
        student_competences[student] = comp

    top_3 = sorted(students, key=lambda s: student_competences[s], reverse=True)[:3]

    records = []
    for student in students:
        is_top = student in top_3
        comp = student_competences[student]
        for subject in subjects:
            if is_top:
                mark = rng.randint(89, 100) if rng.random() < 0.8 else comp + rng.normal(5, 4)
            else:
                mark = comp + rng.normal(0, 6)
            records.append({
                "Student": student,
                "Subject": subject,
                "Mark": int(np.clip(mark, 60, 99))
            })

    return pd.DataFrame(records)


# get class data by term
def get_class_data_by_term(class_name: str, term_index: int = 0) -> pd.DataFrame:
    """Get term-specific class data with session-state caching."""
    cache_key = f"data_{class_name}_t{term_index}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]
    df = generate_class_data_by_term(class_name, term_index)
    st.session_state[cache_key] = df
    return df


@st.cache_data
# get all class averages cached
def get_all_class_averages_cached() -> dict:
    """
    Compute the overall average mark for every class (for section ranking).
    Cached via st.cache_data for performance — called once per session.
    """
    avgs = {}
    for cls in ALL_CLASSES:
        df = generate_class_data(cls)
        avgs[cls] = round(float(df["Mark"].mean()), 1) if not df.empty else 0.0
    return avgs
