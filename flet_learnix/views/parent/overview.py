from services.db_services import get_total_subjects_count, resolve_student_id, get_term_row, get_subjects
import flet as ft
import flet_charts as fc
from components.banner import build_stat_row
from components.section_header import build_section_header
from components.data_table import build_data_table
from components.dialogs import build_notice
from constants import QUARTERS, COMPONENTS
from services.analytics import (
    get_student_term_subject_scores_df,
    is_quarter_complete_for_student,
    get_student_component_grades_df,
    _parent_component_value_for_analytics,
    load_component_scores,
)
import pandas as pd
import numpy as np


# ── Colour palette for each component line ──────────────────────────────────
_COMP_COLORS = {
    "Worksheet (0-10)":    "#10b981",  # green
    "Test (0-10)":         "#ef4444",  # red
    "Mid Exam (0-30)":     "#f59e0b",  # amber
    "Final Exam (0-40)":   "#3b82f6",  # blue
    "Assignment (0-10)":   "#a855f7",  # purple
}


def _build_multi_line_component_chart(student_name: str) -> ft.Control:
    """Build Component Score Trends Across Quarters (one line per component)."""
    comp_keys = list(COMPONENTS.keys())
    sid = resolve_student_id(student_name)

    # Gather average component score per quarter per component type
    series_data: dict[str, list] = {c: [] for c in comp_keys}
    q_labels = QUARTERS
    has_any_global = False

    for q in QUARTERS:
        trow = get_term_row(q)
        has_any = False
        comp_totals: dict[str, list] = {c: [] for c in comp_keys}
        
        if trow:
            term_id = trow["id"]
            subs = [s for s in get_subjects() if s["name"] != "__TERM_ATT__"]
            for sub in subs:
                if sid is None:
                    continue
                loaded = load_component_scores(sid, sub["id"], term_id)
                for comp in comp_keys:
                    av = _parent_component_value_for_analytics(loaded.get(comp))
                    if av is not None:
                        comp_totals[comp].append(av)
                        has_any = True
                        
        if has_any:
            has_any_global = True
            for comp in comp_keys:
                vals = comp_totals[comp]
                series_data[comp].append(np.mean(vals) if vals else np.nan)
        else:
            for comp in comp_keys:
                series_data[comp].append(np.nan)

    if not has_any_global:
        return ft.Text("No component data recorded yet.", color="#64748b", italic=True)

    max_y = 0.0
    for vlist in series_data.values():
        for v in vlist:
            if isinstance(v, float) and not np.isnan(v) and v > max_y:
                max_y = v
    if max_y == 0:
        max_y = 40

    # Build one fc.LineChartData per component
    all_series = []
    legend_chips = []
    for comp in comp_keys:
        color = _COMP_COLORS.get(comp, "#64748b")
        pts = []
        for i, v in enumerate(series_data[comp]):
            if not (isinstance(v, float) and np.isnan(v)):
                pts.append(fc.LineChartDataPoint(i, v))
        if pts:
            all_series.append(
                fc.LineChartData(
                    points=pts,
                    stroke_width=3,
                    color=color,
                    curved=True,
                    rounded_stroke_cap=True,
                    point=True,
                )
            )
            legend_chips.append(
                ft.Row([
                    ft.Container(width=18, height=4, bgcolor=color, border_radius=2),
                    ft.Text(comp, size=11, color="#334155")
                ], spacing=6)
            )

    chart = fc.LineChart(
        data_series=all_series,
        border=ft.Border.all(1, "#e2e8f0"),
        left_axis=fc.ChartAxis(label_size=40, title=ft.Text("score")),
        bottom_axis=fc.ChartAxis(
            labels=[
                fc.ChartAxisLabel(
                    value=i,
                    label=ft.Container(ft.Text(q_labels[i], size=11), padding=5)
                )
                for i in range(len(q_labels))
            ],
            label_size=40,
            title=ft.Text("Quarter"),
        ),
        horizontal_grid_lines=fc.ChartGridLines(color="#e2e8f0", width=1, dash_pattern=[3, 3]),
        max_y=max_y * 1.15,
        min_y=0,
        min_x=0,
        max_x=3,
        interactive=True,
    )

    return ft.Column([
        ft.Text("Component Score Trends Across Quarters", size=18, weight="bold", color="#0f172a"),
        ft.Row(controls=legend_chips, spacing=16, run_spacing=6, wrap=True),
        ft.Container(content=chart, height=320, padding=20, bgcolor="#ffffff",
                     border_radius=12, border=ft.Border.all(1, "#e2e8f0")),
    ], spacing=10)


def _build_performance_journey(df_grades: pd.DataFrame, completed_quarters: list) -> ft.Control:
    """Annual Academic Progress line chart + Trend Analysis card."""
    if len(completed_quarters) < 1:
        return ft.Container()

    # Enforce QUARTERS order structurally so the X-axis plots all 4 Quarters unconditionally
    scores = []
    q_labels = QUARTERS
    for q in QUARTERS:
        if q in completed_quarters:
            # Get the mean of scores for this specific quarter
            q_mean = df_grades[(df_grades["Quarter"] == q) & (df_grades["score"].notna())]["score"].mean()
            scores.append(q_mean)
        else:
            scores.append(np.nan)

    # Build data points ignoring NaN
    pts = []
    valid_scores = []
    for i, s in enumerate(scores):
        if not np.isnan(s):
            pts.append(fc.LineChartDataPoint(i, round(s, 2)))
            valid_scores.append(s)

    chart = fc.LineChart(
        data_series=[
            fc.LineChartData(
                points=pts,
                stroke_width=4,
                color="#7c3aed",
                curved=False,
                rounded_stroke_cap=True,
                point=True,
            )
        ],
        border=ft.Border.all(1, "#e2e8f0"),
        left_axis=fc.ChartAxis(label_size=40, title=ft.Text("score")),
        bottom_axis=fc.ChartAxis(
            labels=[
                fc.ChartAxisLabel(
                    value=i,
                    label=ft.Container(ft.Text(q_labels[i], size=11), padding=5)
                )
                for i in range(len(q_labels))
            ],
            label_size=40,
            title=ft.Text("Quarter"),
        ),
        horizontal_grid_lines=fc.ChartGridLines(color="#e2e8f0", width=1, dash_pattern=[3, 3]),
        max_y=max(valid_scores) * 1.1 if valid_scores else 100,
        min_y=max(0, min(valid_scores) * 0.9) if valid_scores else 0,
        min_x=0,
        max_x=3,
        interactive=True,
    )

    chart_card = ft.Container(
        content=ft.Column([
            ft.Text("Annual Academic Progress", size=18, weight="bold", color="#0f172a"),
            ft.Container(content=chart, height=300, padding=20,
                         bgcolor="#ffffff", border_radius=12, border=ft.Border.all(1, "#e2e8f0")),
        ], spacing=10),
        expand=True,
    )

    # Trend analysis card
    if len(scores) >= 2:
        diff = scores[-1] - scores[0]
        if diff >= 3:
            trend_label = "Improving"
            trend_color = "#10b981"
            trend_bg = "#ecfdf5"
        elif diff <= -3:
            trend_label = "Declining"
            trend_color = "#ef4444"
            trend_bg = "#fef2f2"
        else:
            trend_label = "Stable"
            trend_color = "#f59e0b"
            trend_bg = "#fffbeb"

        # Simple linear extrapolation to predict final trajectory
        if len(scores) >= 2:
            slope = (scores[-1] - scores[0]) / max(len(scores) - 1, 1)
            steps_remaining = 4 - len(scores)
            predicted = scores[-1] + slope * steps_remaining
            predicted = round(max(0, min(100, predicted)))
        else:
            predicted = round(scores[-1])
    else:
        trend_label = "Stable"
        trend_color = "#f59e0b"
        trend_bg = "#fffbeb"
        predicted = round(scores[0]) if scores else 0

    trend_card = ft.Container(
        content=ft.Column([
            ft.Text("Trend analysis", size=18, weight="bold", color="#0f172a"),
            ft.Text("Based on all completed quarters:", size=13, color="#64748b"),
            ft.Container(height=10),
            ft.Container(
                content=ft.Text(trend_label, size=14, weight="bold", color=trend_color),
                bgcolor=trend_bg,
                padding=ft.padding.symmetric(horizontal=14, vertical=6),
                border_radius=20,
                border=ft.Border.all(1, trend_color),
            ),
            ft.Container(height=16),
            ft.Text("Predicted final trajectory", size=14, color="#334155", weight="bold"),
            ft.Text(f"~{predicted}", size=40, weight="bold", color="#7c3aed"),
        ], spacing=4),
        width=220,
        padding=24,
        bgcolor="#ffffff",
        border_radius=12,
        border=ft.Border.all(1, "#e2e8f0"),
    )

    return ft.Row([chart_card, trend_card], spacing=20, vertical_alignment=ft.CrossAxisAlignment.START)


def build_parent_overview(page: ft.Page, app_state) -> ft.View:
    student_name = (app_state.auth.user_name or "Student").title()
    df_grades = get_student_term_subject_scores_df(student_name)

    if df_grades.empty:
        return ft.View(route="/parent/overview", controls=[ft.Text("No academic records available yet.")])

    total_subjects = get_total_subjects_count()
    if total_subjects == 0:
        return ft.View(route="/parent/overview", controls=[ft.Text("System configuration error: No valid subjects defined.")])

    completed_quarters_list = [q for q in QUARTERS if is_quarter_complete_for_student(student_name, q)]
    num_complete = len(completed_quarters_list)
    all_complete = (num_complete == 4)

    controls = []

    if all_complete:
        df_comp = df_grades[df_grades["score"].notna()].copy()
        subject_avgs = df_comp.groupby("Subject")["score"].mean()
        overall_avg = df_comp["score"].mean()
        best_sub = subject_avgs.idxmax()
        best_sco = subject_avgs.max()
        weak_sub = subject_avgs.idxmin()
        weak_sco = subject_avgs.min()

        controls.append(build_stat_row([
            {"label": "Overall Average", "value": f"{overall_avg:.1f}", "note": "All 4 quarters"},
            {"label": "Best Subject", "value": best_sub, "note": f"Avg: {best_sco:.1f}"},
            {"label": "Weakest Subject", "value": weak_sub, "note": f"Avg: {weak_sco:.1f}"},
            {"label": "Performance", "value": "Complete", "note": "Full analytics av."}
        ]))

        weak_list = subject_avgs[subject_avgs < 60].index.tolist()
        if len(weak_list) >= 2:
            controls.append(build_notice("Immediate Attention Required",
                                         f"Multiple subjects average below 60: {', '.join(weak_list)}.", tone="critical"))
        elif len(weak_list) == 1:
            controls.append(build_notice("Performance Improvement Required",
                                         f"{weak_list[0]} averages below 60.", tone="warning"))
    else:
        q_str = ", ".join(completed_quarters_list) if completed_quarters_list else "None"
        controls.append(build_stat_row([
            {"label": "Overall Average", "value": "Incomplete", "note": "Awaiting quarters"},
            {"label": "Best Subject", "value": "Incomplete", "note": "-"},
            {"label": "Weakest Subject", "value": "Incomplete", "note": "-"},
            {"label": "Performance Status", "value": "Incomplete", "note": f"{num_complete}/4 complete ({q_str})"}
        ]))
        controls.append(build_notice("Yearly Insights Locked",
                                     f"Full yearly analysis unlocks once all 4 quarters are recorded. Currently {num_complete}/4 complete.",
                                     tone="warning"))

    controls.append(ft.Divider(height=30))

    # ── Component Score Trends Across Quarters ───────────────────────────
    controls.append(build_section_header("Component Trend Overview",
                                         "Cross-quarter trends per assessment type. Available regardless of overall completeness."))
    controls.append(_build_multi_line_component_chart(student_name))

    controls.append(ft.Divider(height=30))

    # ── Full Performance Journey (only when at least 1 quarter complete) ─
    if completed_quarters_list:
        controls.append(build_section_header("Full Performance Journey",
                                             "Complete annual academic trajectory and trend predictions."))
        controls.append(_build_performance_journey(df_grades, completed_quarters_list))
        controls.append(ft.Divider(height=30))

    # ── Detailed Breakdown table ─────────────────────────────────────────
    controls.append(build_section_header("Detailed Breakdown", "Numerical records across all evaluated quarters."))
    grade_table = df_grades.pivot(index="Subject", columns="Quarter", values="score").reset_index()
    for q in QUARTERS:
        if q not in grade_table.columns:
            grade_table[q] = np.nan

    if all_complete:
        grade_table["Yearly Avg"] = grade_table[QUARTERS].mean(axis=1)

    controls.append(build_data_table(grade_table))

    return ft.View(route="/parent/overview", controls=controls)
