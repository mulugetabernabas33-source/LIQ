"""
Analytics module for computing statistics and insights from student data.
Provides functions for averages, rankings, and performance predictions.
"""

# file connections / imports
import pandas as pd
import numpy as np


# get class avg per subject
def get_class_avg_per_subject(df: pd.DataFrame) -> pd.Series:
    """
    Compute average mark per subject, sorted descending.

    Args:
        df: DataFrame with columns ["Student", "Subject", "Mark"]

    Returns:
        Series with subject names as index and average marks as values
    """
    return df.groupby("Subject")["Mark"].mean().sort_values(ascending=False)


# get strongest weakest
def get_strongest_weakest(df: pd.DataFrame) -> tuple:
    """
    Identify the strongest and weakest subjects by average mark.

    Args:
        df: DataFrame with columns ["Student", "Subject", "Mark"]

    Returns:
        Tuple of (strongest_subject_name, weakest_subject_name)
    """
    avg_per_subject = get_class_avg_per_subject(df)
    strongest = avg_per_subject.idxmax()
    weakest = avg_per_subject.idxmin()
    return (strongest, weakest)


# get class overall avg
def get_class_overall_avg(df: pd.DataFrame) -> float:
    """
    Compute overall class average across all marks.

    Args:
        df: DataFrame with columns ["Student", "Subject", "Mark"]

    Returns:
        Overall average rounded to 1 decimal place
    """
    return round(df["Mark"].mean(), 1)


# get student count
def get_student_count(df: pd.DataFrame) -> int:
    """
    Count unique students in the dataset.

    Args:
        df: DataFrame with columns ["Student", "Subject", "Mark"]

    Returns:
        Number of unique students
    """
    return df["Student"].nunique()


# get top n students
def get_top_n_students(df: pd.DataFrame, n: int = 3) -> pd.DataFrame:
    """
    Get top N students by average mark across all subjects.

    Args:
        df: DataFrame with columns ["Student", "Subject", "Mark"]
        n: Number of top students to return (default: 3)

    Returns:
        DataFrame with Student, Average, and individual subject mark columns
    """
    student_avg = df.groupby("Student")["Mark"].mean()

    top_students = student_avg.nlargest(n).index.tolist()

    top_df = df[df["Student"].isin(top_students)]
    pivot_df = top_df.pivot(index="Student", columns="Subject", values="Mark")

    pivot_df["Average"] = student_avg[top_students]

    pivot_df = pivot_df.sort_values("Average", ascending=False)
    pivot_df = pivot_df.reset_index()

    cols = pivot_df.columns.tolist()
    cols.remove("Average")
    cols.insert(1, "Average")
    pivot_df = pivot_df[cols]

    return pivot_df


# get grade top students
def get_grade_top_students(grade: int, n: int = 3) -> pd.DataFrame:
    """
    Get top N students across all classes in a grade.

    Args:
        grade: Grade number (9, 10, 11, or 12)
        n: Number of top students to return (default: 3)

    Returns:
        DataFrame with columns: ["Student", "Class", "Average"]
    """
    from .data_gen import get_class_data, get_all_classes_for_grade

    classes = get_all_classes_for_grade(grade)

    all_data = []
    for class_name in classes:
        class_df = get_class_data(class_name).copy()
        class_df["Class"] = class_name
        all_data.append(class_df)

    combined_df = pd.concat(all_data, ignore_index=True)

    student_summary = combined_df.groupby(["Student", "Class"]).agg(
        Average=("Mark", "mean")
    ).reset_index()

    top_df = student_summary.nlargest(n, "Average")[["Student", "Class", "Average"]]
    top_df["Average"] = top_df["Average"].round(1)

    return top_df.reset_index(drop=True)


# get prediction trend
def get_prediction_trend(df: pd.DataFrame) -> str:
    """
    Generate a performance prediction based on current marks.

    Analyzes overall average and subject-wise performance to provide
    actionable insights and predictions.

    Args:
        df: DataFrame with columns ["Student", "Subject", "Mark"]

    Returns:
        Prediction message string with recommendations
    """
    overall_avg = df["Mark"].mean()

    subject_avg = get_class_avg_per_subject(df)

    weak_subjects = subject_avg[subject_avg < 70].index.tolist()

    critical_subjects = subject_avg[subject_avg < 60].index.tolist()

    if overall_avg >= 75:
        return (
            "Strong overall performance. If the current trend continues, "
            "academic results are expected to remain excellent."
        )
    elif overall_avg >= 65:
        weak_list = ", ".join(weak_subjects) if weak_subjects else "none identified"
        return (
            f"Moderate performance. With focused effort on weaker subjects "
            f"({weak_list}), overall results can improve significantly."
        )
    else:
        critical_list = ", ".join(critical_subjects) if critical_subjects else ", ".join(weak_subjects)
        return (
            f"Below-average performance detected. Immediate intervention "
            f"recommended in: {critical_list}."
        )


# get pass rate
def get_pass_rate(df: pd.DataFrame, threshold: float = 60.0) -> float:
    """Percentage of students whose average mark >= threshold."""
    student_avgs = df.groupby("Student")["Mark"].mean()
    if len(student_avgs) == 0:
        return 0.0
    return round(float((student_avgs >= threshold).sum()) / len(student_avgs) * 100, 1)


# get fail rate
def get_fail_rate(df: pd.DataFrame, threshold: float = 60.0) -> float:
    """Percentage of students whose average mark < threshold."""
    return round(100.0 - get_pass_rate(df, threshold), 1)


# get distinction rate
def get_distinction_rate(df: pd.DataFrame, threshold: float = 75.0) -> float:
    """Percentage of students with average mark >= distinction threshold."""
    student_avgs = df.groupby("Student")["Mark"].mean()
    if len(student_avgs) == 0:
        return 0.0
    return round(float((student_avgs >= threshold).sum()) / len(student_avgs) * 100, 1)


# get at risk students
def get_at_risk_students(df: pd.DataFrame, threshold: float = 60.0) -> float:
    """Percentage of students below pass mark (at-risk)."""
    return get_fail_rate(df, threshold)


# get top performer index
def get_top_performer_index(df: pd.DataFrame) -> float:
    """Percentage of students in the top 10% of section by average score."""
    student_avgs = df.groupby("Student")["Mark"].mean()
    total = len(student_avgs)
    if total == 0:
        return 0.0
    top_n = max(1, int(np.ceil(total * 0.1)))
    top_threshold = float(student_avgs.nlargest(top_n).min())
    top_count = float((student_avgs >= top_threshold).sum())
    return round(top_count / total * 100, 1)


# get subject performance gap
def get_subject_performance_gap(df: pd.DataFrame) -> dict:
    """Difference between highest and lowest score per subject (score spread)."""
    result = {}
    for subj in df["Subject"].unique():
        marks = df[df["Subject"] == subj]["Mark"]
        result[str(subj)] = round(float(marks.max() - marks.min()), 1)
    return result


# get performance variance
def get_performance_variance(df: pd.DataFrame) -> float:
    """Statistical variance of per-student average scores."""
    student_avgs = df.groupby("Student")["Mark"].mean()
    if len(student_avgs) < 2:
        return 0.0
    return round(float(student_avgs.var()), 2)


# get engagement level
def get_engagement_level(df: pd.DataFrame) -> float:
    """Proxy engagement: percentage of students with avg >= 65 (active baseline)."""
    student_avgs = df.groupby("Student")["Mark"].mean()
    total = len(student_avgs)
    if total == 0:
        return 0.0
    return round(float((student_avgs >= 65).sum()) / total * 100, 1)


# get section ranking
def get_section_ranking(class_name: str, all_class_avgs: dict) -> int:
    """1-indexed rank of class_name among all classes (1 = best performer)."""
    if not all_class_avgs or class_name not in all_class_avgs:
        return 0
    sorted_cls = sorted(all_class_avgs.items(), key=lambda x: x[1], reverse=True)
    for rank, (cls, _) in enumerate(sorted_cls, 1):
        if cls == class_name:
            return rank
    return 0


# get term improvement
def get_term_improvement(df_t1: pd.DataFrame, df_t2: pd.DataFrame) -> float:
    """Percentage change in avg score from term 1 to term 2. Positive = improvement."""
    if df_t1.empty or df_t2.empty:
        return 0.0
    avg1 = float(df_t1["Mark"].mean())
    avg2 = float(df_t2["Mark"].mean())
    if avg1 == 0:
        return 0.0
    return round((avg2 - avg1) / avg1 * 100, 2)
