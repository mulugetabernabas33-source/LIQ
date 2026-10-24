import pandas as pd
import numpy as np

from constants import COMPONENTS, ALL_ROWS, ATTENDANCE_ROW, QUARTERS
from services.db_services import (
    get_db_connection,
    get_subjects,
    get_student_row,
    get_subject_row,
    get_term_row,
    resolve_student_id,
    load_student_attendance_code,
)

def _is_blank_markbook_value(val) -> bool:
    if val is None:
        return True
    if isinstance(val, (float, np.floating)) and np.isnan(val):
        return True
    s = str(val).strip()
    if s == "" or s.lower() == "nan":
        return True
    if s == "-":
        return True
    return False

def _parse_component_score(raw):
    if _is_blank_markbook_value(raw):
        return None
    try:
        return float(raw)
    except (ValueError, TypeError):
        return None

def _parent_component_value_for_analytics(raw):
    if raw is None:
        return None
    try:
        if isinstance(raw, (float, np.floating)) and np.isnan(raw):
            return None
        fv = float(raw)
    except (TypeError, ValueError):
        return None
    if fv == 0.0:
        return None
    return fv

def save_component_scores(student_id: int, subject_id: int, term_id: int, component_scores: dict):
    conn = get_db_connection()
    if conn is None:
        return
    try:
        c = conn.cursor()
        total = 0.0
        recorded = 0
        for component, raw in component_scores.items():
            max_val = COMPONENTS.get(component, 100)
            parsed = _parse_component_score(raw)
            if parsed is None:
                c.execute(
                    """
                    DELETE FROM component_grades
                    WHERE student_id = ? AND subject_id = ? AND term_id = ? AND component = ?
                """,
                    (student_id, subject_id, term_id, component),
                )
                continue
            score = max(0.0, min(float(parsed), float(max_val)))
            total += score
            recorded += 1
            c.execute(
                """
                INSERT OR REPLACE INTO component_grades
                    (student_id, subject_id, term_id, component, score)
                VALUES (?, ?, ?, ?, ?)
            """,
                (student_id, subject_id, term_id, component, score),
            )
        if recorded == 0:
            c.execute(
                """
                DELETE FROM grades
                WHERE student_id = ? AND subject_id = ? AND term_id = ?
            """,
                (student_id, subject_id, term_id),
            )
        else:
            c.execute(
                """
                INSERT OR REPLACE INTO grades (student_id, subject_id, term_id, score)
                VALUES (?, ?, ?, ?)
            """,
                (student_id, subject_id, term_id, total),
            )
        conn.commit()
    finally:
        conn.close()

def load_component_scores(student_id: int, subject_id: int, term_id: int) -> dict:
    conn = get_db_connection()
    if conn is None:
        return {}
    try:
        c = conn.cursor()
        c.execute(
            """
            SELECT component, score
            FROM component_grades
            WHERE student_id = ? AND subject_id = ? AND term_id = ?
        """,
            (student_id, subject_id, term_id),
        )
        return {row["component"]: row["score"] for row in c.fetchall()}
    finally:
        conn.close()

def get_all_grades_df() -> pd.DataFrame:
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    try:
        return pd.read_sql_query(
            """
            SELECT s.name AS Student, sub.name AS Subject,
                   t.name AS Quarter, g.score
            FROM grades g
            JOIN students s   ON g.student_id = s.id
            JOIN subjects sub ON g.subject_id = sub.id
            JOIN terms t      ON g.term_id    = t.id
            WHERE sub.name != '__TERM_ATT__'
        """,
            conn,
        )
    finally:
        conn.close()

def get_all_attendance_df() -> pd.DataFrame:
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    try:
        return pd.read_sql_query(
            """
            SELECT s.name AS Student, a.attendance_percentage
            FROM attendance a
            JOIN students s   ON a.student_id = s.id
            JOIN subjects sub ON a.subject_id = sub.id
            WHERE sub.name = '__TERM_ATT__'
        """,
            conn,
        )
    finally:
        conn.close()

def compute_dashboard_data():
    df_grades = get_all_grades_df()
    df_att = get_all_attendance_df()

    empty_ranking = pd.DataFrame(
        columns=[
            "Student", "Q1", "Q2", "Q3", "Q4", 
            "Q1 Rank", "Q2 Rank", "Q3 Rank", "Q4 Rank", 
            "Overall Avg", "Overall Rank",
        ]
    )
    empty_att = pd.DataFrame(columns=["Student", "Attendance %"])

    if df_grades.empty:
        return (
            pd.Series(dtype=float),
            pd.DataFrame(columns=["Quarter", "Average Score"]),
            [],
            empty_ranking,
            empty_att,
            pd.DataFrame(),
            pd.DataFrame(columns=["Student", "Quarter", "Average"]),
        )

    avg_subject = (
        df_grades.groupby("Subject")["score"].mean().sort_values(ascending=False)
    )
    weak_subjects = avg_subject[avg_subject < 60].index.tolist()

    perf = (
        df_grades.groupby(["Student", "Quarter"])["score"]
        .mean()
        .reset_index()
        .rename(columns={"score": "Average"})
    )

    quarterly_trend = (
        perf.groupby("Quarter")["Average"]
        .mean()
        .reset_index()
        .rename(columns={"Average": "Average Score"})
    )

    ranking_table = perf.pivot(
        index="Student", columns="Quarter", values="Average"
    ).reset_index()
    for q in QUARTERS:
        if q not in ranking_table.columns:
            ranking_table[q] = np.nan
    ranking_table["Overall Avg"] = ranking_table[QUARTERS].mean(axis=1)
    for q in QUARTERS:
        ranking_table[f"{q} Rank"] = ranking_table[q].rank(
            ascending=False, na_option="bottom"
        )
    ranking_table["Overall Rank"] = ranking_table["Overall Avg"].rank(ascending=False)

    if not df_att.empty:
        attendance_pct = (
            df_att.groupby("Student")["attendance_percentage"]
            .mean()
            .reset_index()
            .rename(columns={"attendance_percentage": "Attendance %"})
        )
        q_att_pivot = pd.DataFrame(index=df_grades["Student"].unique())
    else:
        attendance_pct = empty_att
        q_att_pivot = pd.DataFrame()

    return (
        avg_subject,
        quarterly_trend,
        weak_subjects,
        ranking_table,
        attendance_pct,
        q_att_pivot,
        perf,
    )

def build_student_markbook_df(student_id: int, term_id: int, subjects: list) -> pd.DataFrame:
    data = {"Components": ALL_ROWS}
    for subj in subjects:
        data[subj] = [""] * len(ALL_ROWS)
    df = pd.DataFrame(data).set_index("Components")

    for subj in subjects:
        sub_row = get_subject_row(subj)
        if sub_row is None:
            continue
        subject_id = sub_row["id"]
        scores = load_component_scores(student_id, subject_id, term_id)
        for comp in COMPONENTS:
            if comp in scores and scores[comp] is not None:
                v = scores[comp]
                df.at[comp, subj] = str(int(v)) if float(v) == int(float(v)) else str(v)

    att_code = load_student_attendance_code(student_id)
    for subj in subjects:
        df.at[ATTENDANCE_ROW, subj] = att_code

    return df

def compute_student_totals(df: pd.DataFrame) -> pd.Series:
    numeric = df.drop(index=ATTENDANCE_ROW, errors="ignore").copy()
    totals = {}
    for col in numeric.columns:
        s = 0.0
        for comp in COMPONENTS:
            if comp not in numeric.index:
                continue
            raw = numeric.at[comp, col]
            if _is_blank_markbook_value(raw):
                continue
            try:
                s += float(raw)
            except (ValueError, TypeError):
                continue
        totals[col] = s
    return pd.Series(totals)

def get_student_grades_df(student_name: str) -> pd.DataFrame:
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    try:
        query = """
            SELECT sub.name AS Subject, t.name AS Quarter, g.score
            FROM grades g
            JOIN students s   ON g.student_id = s.id
            JOIN subjects sub ON g.subject_id = sub.id
            JOIN terms t      ON g.term_id    = t.id
            WHERE (s.name = ? OR s.name = ? OR s.name = ?)
              AND sub.name != '__TERM_ATT__'
        """
        alt_name1 = student_name.replace(" ", ".")
        alt_name2 = student_name.replace(".", " ")
        df = pd.read_sql_query(query, conn, params=(student_name, alt_name1, alt_name2))
        return df
    finally:
        conn.close()

def get_student_notes_df(student_name: str) -> pd.DataFrame:
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    try:
        query = """
            SELECT t.note, t.date_recorded
            FROM teacher_notes t
            JOIN students s ON t.student_id = s.id
            WHERE (s.name = ? OR s.name = ? OR s.name = ?)
            ORDER BY t.date_recorded DESC
        """
        alt_name1 = student_name.replace(" ", ".")
        alt_name2 = student_name.replace(".", " ")
        df = pd.read_sql_query(query, conn, params=(student_name, alt_name1, alt_name2))
        return df
    finally:
        conn.close()

def get_student_component_grades_df(student_name: str, quarter: str) -> pd.DataFrame:
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    try:
        query = """
            SELECT sub.name AS Subject, cg.component AS Component, cg.score
            FROM component_grades cg
            JOIN students s   ON cg.student_id = s.id
            JOIN subjects sub ON cg.subject_id = sub.id
            JOIN terms t      ON cg.term_id    = t.id
            WHERE (s.name = ? OR s.name = ? OR s.name = ?)
              AND t.name = ?
              AND sub.name != '__TERM_ATT__'
        """
        alt_name1 = student_name.replace(" ", ".")
        alt_name2 = student_name.replace(".", " ")
        df = pd.read_sql_query(
            query, conn, params=(student_name, alt_name1, alt_name2, quarter)
        )
        return df
    finally:
        conn.close()

def subject_has_all_components(student_id: int, term_id: int, subject_id: int) -> bool:
    loaded = load_component_scores(student_id, subject_id, term_id)
    for comp in COMPONENTS:
        if _parent_component_value_for_analytics(loaded.get(comp)) is None:
            return False
    return True

def is_quarter_complete_for_student(student_name: str, quarter: str) -> bool:
    sid = resolve_student_id(student_name)
    if sid is None:
        return False
    trow = get_term_row(quarter)
    if not trow:
        return False
    term_id = trow["id"]
    subs = [s for s in get_subjects() if s["name"] != "__TERM_ATT__"]
    if not subs:
        return False
    for sub in subs:
        if not subject_has_all_components(sid, term_id, sub["id"]):
            return False
    return True

def get_student_term_subject_scores_df(student_name: str) -> pd.DataFrame:
    sid = resolve_student_id(student_name)
    if sid is None:
        return pd.DataFrame(columns=["Subject", "Quarter", "score"])
    rows = []
    for q in QUARTERS:
        trow = get_term_row(q)
        if not trow:
            continue
        term_id = trow["id"]
        for sub in get_subjects():
            if sub["name"] == "__TERM_ATT__":
                continue
            if not subject_has_all_components(sid, term_id, sub["id"]):
                rows.append({"Subject": sub["name"], "Quarter": q, "score": np.nan})
                continue
            loaded = load_component_scores(sid, sub["id"], term_id)
            total = sum(
                _parent_component_value_for_analytics(loaded[c]) for c in COMPONENTS if loaded.get(c) is not None
            )
            rows.append({"Subject": sub["name"], "Quarter": q, "score": total})
    return pd.DataFrame(rows)

def build_full_component_pivot(student_name: str, quarter: str) -> pd.DataFrame:
    sid = resolve_student_id(student_name)
    trow = get_term_row(quarter)
    if sid is None or not trow:
        return pd.DataFrame()
    term_id = trow["id"]
    subs = [s for s in get_subjects() if s["name"] != "__TERM_ATT__"]
    records = []
    for sub in subs:
        loaded = load_component_scores(sid, sub["id"], term_id)
        row = {"Subject": sub["name"]}
        vals = []
        all_filled = True
        for comp in COMPONENTS:
            av = _parent_component_value_for_analytics(loaded.get(comp))
            if av is None:
                row[comp] = np.nan
                all_filled = False
            else:
                row[comp] = av
                vals.append(av)
        if all_filled and len(vals) == len(COMPONENTS):
            row["Total Output"] = sum(vals)
        else:
            row["Total Output"] = np.nan
        records.append(row)
    return pd.DataFrame(records)

def build_component_subject_frame_for_parent(student_name: str, quarter: str, component_key: str) -> pd.DataFrame:
    sid = resolve_student_id(student_name)
    trow = get_term_row(quarter)
    if sid is None or not trow:
        return pd.DataFrame(columns=["Subject", "score"])
    term_id = trow["id"]
    subs = [s for s in get_subjects() if s["name"] != "__TERM_ATT__"]
    rows = []
    for sub in subs:
        loaded = load_component_scores(sid, sub["id"], term_id)
        av = _parent_component_value_for_analytics(loaded.get(component_key))
        rows.append({"Subject": sub["name"], "score": np.nan if av is None else av})
    return pd.DataFrame(rows)

def count_parent_filled_component_slots(student_name: str, quarter: str) -> int:
    sid = resolve_student_id(student_name)
    trow = get_term_row(quarter)
    if sid is None or not trow:
        return 0
    term_id = trow["id"]
    n = 0
    for sub in get_subjects():
        if sub["name"] == "__TERM_ATT__":
            continue
        loaded = load_component_scores(sid, sub["id"], term_id)
        for comp in COMPONENTS:
            if _parent_component_value_for_analytics(loaded.get(comp)) is not None:
                n += 1
    return n

def generate_ai_insight(current_avg, prev_avg):
    if prev_avg is None:
        return "Stable early performance baseline."
    diff = current_avg - prev_avg
    if diff >= 3:
        return "Performance has improved compared to last quarter."
    elif diff <= -3:
        return "Performance has declined in recent quarters."
    else:
        return "Performance remains stable."
