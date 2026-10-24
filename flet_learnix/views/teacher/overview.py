import pandas as pd
import flet as ft
from components.banner import build_banner, build_stat_row
from components.section_header import build_section_header
from components.charts import build_bar_chart, build_line_chart
from components.data_table import build_data_table
from components.dialogs import build_notice
from services.analytics import compute_dashboard_data

def build_teacher_overview(page: ft.Page, app_state) -> ft.View:
    (
        avg_subject,
        quarterly_trend,
        weak_subjects,
        ranking_table,
        attendance_pct,
        q_att_pivot,
        perf,
    ) = compute_dashboard_data()

    has_data = not ranking_table.empty

    teacher_name = app_state.auth.user_name or "Teacher"
    classroom = app_state.selections.classroom
    school = app_state.selections.school

    banner = build_banner(
        f"Teacher Dashboard: {classroom}",
        "Classroom analytics, performance trends, and alerts.",
        "STAFF PORTAL",
        meta_items=[f"Teacher: {teacher_name}", f"Class: {classroom}", "Real-time Metrics"],
        panel_label="Total Students",
        panel_value=str(len(ranking_table)) if has_data else "0",
        panel_note="Registered in DB"
    )


    # Guard: if no grade data at all, show a clean empty state instead of crashing
    if not has_data:
        return ft.View(route="/teacher/overview", controls=[
            banner,
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.INFO_OUTLINE, size=48, color="#94a3b8"),
                    ft.Text("No grade data yet.", size=20, weight="bold", color="#475569"),
                    ft.Text("Go to a Quarter markbook to enter student scores.", color="#94a3b8")
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
                padding=60, alignment=ft.Alignment(0, 0)
            )
        ])

    # Top KPI calc — safe with NaN check BEFORE calling idxmax
    cls_avg = ranking_table["Overall Avg"].mean()
    cls_avg_str = f"{cls_avg:.1f}" if pd.notna(cls_avg) else "N/A"
    perf_count = len(ranking_table[ranking_table["Overall Avg"] >= 80])
    strongest_subject = avg_subject.index[0] if not avg_subject.empty else "N/A"
    strongest_score = avg_subject.values[0] if not avg_subject.empty else 0.0
    att_avg = attendance_pct["Attendance %"].mean() if not attendance_pct.empty else 0.0

    has_top = ranking_table["Overall Avg"].notna().any()
    if has_top:
        top_student_idx = ranking_table["Overall Avg"].idxmax()
        top_student_name = ranking_table.loc[top_student_idx, "Student"]
        top_student_score = ranking_table.loc[top_student_idx, "Overall Avg"]
    else:
        top_student_name = "N/A"
        top_student_score = 0.0

    stats = build_stat_row([
        {"label": "Class Average", "value": f"{cls_avg:.1f}", "note": "Across all records"},
        {"label": "Strongest Subject", "value": strongest_subject, "note": f"Avg: {strongest_score:.1f}"},
        {"label": "Attendance", "value": f"{att_avg:.1f}%", "note": "Yearly avg rate"},
        {"label": "Top Student", "value": top_student_name, "note": f"Avg: {top_student_score:.1f}"}
    ])

    # Convert avg_subject Series to DataFrame for chart
    df_avg_sub = avg_subject.reset_index()
    df_avg_sub.columns = ["Subject", "Average Score"]
    bar_chart = build_bar_chart(df_avg_sub, "Subject", "Average Score")
    line_chart = build_line_chart(quarterly_trend, "Quarter", "Average Score")

    sem1 = perf[perf["Quarter"].isin(["Q1", "Q2"])].groupby("Student")["Average"].mean().reset_index()
    sem2 = perf[perf["Quarter"].isin(["Q3", "Q4"])].groupby("Student")["Average"].mean().reset_index()
    
    sem1 = sem1.sort_values("Average", ascending=False).head(5).rename(columns={"Average": "Sem 1 Avg"})
    sem2 = sem2.sort_values("Average", ascending=False).head(5).rename(columns={"Average": "Sem 2 Avg"})
    yearly = ranking_table[["Student", "Overall Avg"]].sort_values("Overall Avg", ascending=False).head(5)

    alert_box = build_notice(
        "Weak subjects detected" if weak_subjects else "Healthy subject performance",
        f"Average below 60 in: {', '.join(weak_subjects)}." if weak_subjects else "All subjects are above 60 points.",
        tone="warning" if weak_subjects else "positive"
    )

    controls = [
        banner,
        stats,
        build_section_header("Performance Overview", "Class trend and subject distribution."),
        ft.Row([ft.Container(content=bar_chart, expand=4), ft.Container(content=line_chart, expand=3)]),
        build_section_header("Subject Alerts", "Subjects needing intervention."),
        alert_box,
        build_section_header("Recognition Snapshot", "Top performers by semester."),
        ft.Row([
            ft.Container(content=ft.Column([ft.Text("Top 5: 1st Semester", weight="bold"), build_data_table(sem1)]), expand=1),
            ft.Container(content=ft.Column([ft.Text("Top 5: 2nd Semester", weight="bold"), build_data_table(sem2)]), expand=1),
            ft.Container(content=ft.Column([ft.Text("Top 5: Full Year", weight="bold"), build_data_table(yearly)]), expand=1)
        ]),
        build_section_header("Class Rankings", "Quarter-by-quarter comparison and overall standing."),
        build_data_table(ranking_table, expand=True)
    ]

    return ft.View(route="/teacher/overview", controls=controls)
