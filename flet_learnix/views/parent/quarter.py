import flet as ft
import flet_charts as fc
import pandas as pd
import numpy as np
from components.section_header import build_section_header
from components.data_table import build_data_table
from components.dialogs import build_notice
from services.analytics import (
    is_quarter_complete_for_student,
    build_full_component_pivot,
)

# Standard colour palette for subjects and charts
_PALETTE = [
    "#10b981", "#84cc16", "#eab308", "#f59e0b",
    "#f97316", "#ef4444", "#8b5cf6", "#3b82f6",
    "#06b6d4", "#ec4899"
]

def _get_badge_info(score: float) -> tuple[str, str, str, str]:
    """Return qualitative rating, text color, bg color, and border color based on score."""
    if score >= 90:
        return "Excellent", "#15803d", "#f0fdf4", "#bbf7d0"
    elif score >= 80:
        return "Very Good", "#1d4ed8", "#eff6ff", "#bfdbfe"
    elif score >= 70:
        return "Good", "#b45309", "#fffbeb", "#fde68a"
    else:
        return "Average", "#b91c1c", "#fef2f2", "#fecaca"

def _build_standings_chart(df: pd.DataFrame, quarter_label: str) -> ft.Control:
    """Build 'Q1 Subject Standings' Bar Chart."""
    df_sorted = df.copy()
    df_sorted = df_sorted[df_sorted["Total Output"].notna()]
    # Force convert to float explicitly to fix Flet types
    df_sorted["Total Output"] = pd.to_numeric(df_sorted["Total Output"], errors='coerce').fillna(0.0).astype(float)
    df_sorted = df_sorted.sort_values(by="Total Output", ascending=False).reset_index(drop=True)
    
    chart_groups = []
    x_labels = []

    for i, (_, row) in enumerate(df_sorted.iterrows()):
        val = float(row["Total Output"])
        # Ensure Flet bar charts don't render native 0 values natively triggering Flutter layout errors.
        if val <= 0:
            val = 0.5 

        sub = str(row["Subject"])
        if len(sub) > 6:
            sub = sub[:5] + "."
            
        color = _PALETTE[i % len(_PALETTE)]
        chart_groups.append(
            fc.BarChartGroup(
                x=i,
                rods=[
                    fc.BarChartRod(
                        from_y=0,
                        to_y=val,
                        width=32,
                        color=color,
                        tooltip=f"{row['Subject']}\n{val:.1f}",
                        border_radius=0,
                    )
                ]
            )
        )
        x_labels.append(
            fc.ChartAxisLabel(
                value=i,
                label=ft.Container(ft.Text(sub, size=11), padding=5, rotate=0.5)
            )
        )
        
    chart = fc.BarChart(
        groups=chart_groups,
        border=ft.Border.all(0, ft.Colors.TRANSPARENT),
        left_axis=fc.ChartAxis(label_size=40, title=ft.Text("score", size=12)),
        bottom_axis=fc.ChartAxis(
            labels=x_labels,
            label_size=40,
            title=ft.Text("Subject", size=12),
        ),
        horizontal_grid_lines=fc.ChartGridLines(color="#e2e8f0", width=1, dash_pattern=[3, 3]),
        max_y=100,
        interactive=True,
    )
    
    return ft.Container(
        content=ft.Column([
            ft.Text(f"{quarter_label.split(' ')[0]} Subject Standings", size=18, weight="bold", color="#0f172a"),
            ft.Container(height=10),
            ft.Container(content=chart, height=260, expand=True)
        ]),
        padding=24,
        bgcolor="#ffffff",
        border_radius=12,
        border=ft.Border.all(1, "#e2e8f0"),
        expand=True
    )

def _build_distribution_chart(df: pd.DataFrame) -> ft.Control:
    """Build 'Performance Distribution' Pie Chart."""
    df_valid = df.copy()
    df_valid = df_valid[df_valid["Total Output"].notna()]
    df_valid["Total Output"] = pd.to_numeric(df_valid["Total Output"], errors='coerce').fillna(0.0).astype(float)
    
    if df_valid.empty:
        return ft.Container()
    
    total_score = float(df_valid["Total Output"].sum())
    sections = []
    legends = []
    
    for i, (_, row) in enumerate(df_valid.iterrows()):
        val = float(row["Total Output"])
        if val <= 0:
            continue
            
        sub = str(row["Subject"])
        pct = (val / total_score * 100) if total_score > 0 else 0
        color = _PALETTE[i % len(_PALETTE)]
        
        sections.append(
            fc.PieChartSection(
                value=val,
                title=f"{pct:.1f}%",
                title_style=ft.TextStyle(size=11, color="#ffffff", weight="bold"),
                color=color,
                radius=60,
            )
        )
        
        legends.append(
            ft.Row([
                ft.Container(width=12, height=12, bgcolor=color, border_radius=2),
                ft.Text(sub[:7], size=11, color="#334155")
            ], spacing=6)
        )

    # Empty chart fix:
    if not sections:
        return ft.Container()

    chart = fc.PieChart(
        sections=sections,
        sections_space=2,
        center_space_radius=40,
        center_space_color="#ffffff",
        expand=True
    )
    
    return ft.Container(
        content=ft.Column([
            ft.Text("Performance Distribution", size=18, weight="bold", color="#0f172a"),
            ft.Container(height=10),
            ft.Row([
                ft.Container(content=chart, width=200, height=200),
                ft.Column(legends, spacing=4)
            ], expand=True, alignment=ft.MainAxisAlignment.CENTER)
        ]),
        padding=24,
        bgcolor="#ffffff",
        border_radius=12,
        border=ft.Border.all(1, "#e2e8f0"),
        width=400
    )


def _build_badges_row(df: pd.DataFrame) -> ft.Control:
    """Build 'Performance Badges' string."""
    df_valid = df[df["Total Output"].notna()].copy()
    
    badges = []
    for _, row in df_valid.iterrows():
        val = row["Total Output"]
        label, t_color, bg_color, br_color = _get_badge_info(val)
        
        badge = ft.Container(
            content=ft.Row([
                ft.Text(str(row["Subject"])[:10], size=13, weight="w600", color="#334155"),
                ft.Text(f"{val:.1f} - {label}", size=13, weight="bold", color=t_color),
            ], spacing=6),
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            bgcolor=bg_color,
            border=ft.Border.all(1, br_color),
            border_radius=20,
        )
        badges.append(badge)
        
    return ft.Column([
        ft.Text("Performance Badges", size=18, weight="bold", color="#0f172a"),
        ft.Row(badges, wrap=True, spacing=10, run_spacing=10)
    ], spacing=10)


from constants import COMPONENTS

def _build_component_expansion_list(df: pd.DataFrame) -> list[ft.Control]:
    """Builds the collapsible rows containing per-component detailed analytic charts and failure warnings."""
    tiles = []
    
    comp_cols = [c for c in df.columns if c not in ("Subject", "Total Output")]
    
    for comp in comp_cols:
        max_score = COMPONENTS.get(comp, 100)
        
        df_comp = df[["Subject", comp]].copy()
        df_comp = df_comp[df_comp[comp].notna()]
        if df_comp.empty:
            continue
            
        df_comp[comp] = pd.to_numeric(df_comp[comp], errors='coerce').fillna(0.0).astype(float)
        
        chart_groups = []
        x_labels = []
        failing_subjects = []
        raw_rows = []
        
        for i, (_, row) in enumerate(df_comp.iterrows()):
            val = float(row[comp])
            sub = str(row["Subject"])
            
            percent = (val / max_score) * 100 if max_score > 0 else 0
            if percent < 60:
                failing_subjects.append(sub)
                
            # Chart data
            disp_val = val if val > 0 else 0.2
            disp_sub = sub[:5] + "." if len(sub) > 6 else sub
            
            chart_groups.append(
                fc.BarChartGroup(
                    x=i,
                    rods=[
                        fc.BarChartRod(from_y=0, to_y=disp_val, width=24, color="#16a34a", tooltip=f"{sub}\n{val:.1f}", border_radius=0)
                    ]
                )
            )
            x_labels.append(fc.ChartAxisLabel(value=i, label=ft.Container(ft.Text(disp_sub, size=10), padding=3, rotate=0.5)))
            
            # Table data
            raw_rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(sub, size=12)),
                    ft.DataCell(ft.Text(f"{val:.1f}", size=12, text_align=ft.TextAlign.RIGHT)),
                ])
            )
            
        chart = fc.BarChart(
            groups=chart_groups,
            border=ft.Border.all(0, ft.Colors.TRANSPARENT),
            left_axis=fc.ChartAxis(label_size=30, title=ft.Text("score", size=11)),
            bottom_axis=fc.ChartAxis(labels=x_labels, label_size=30, title=ft.Text("Subject", size=11)),
            horizontal_grid_lines=fc.ChartGridLines(color="#e2e8f0", width=1, dash_pattern=[3,3]),
            max_y=max_score,
            interactive=True,
        )
        
        chart_container = ft.Container(
            content=ft.Column([
                ft.Text(f"{comp.split(' ')[0]} — Subject Scores", size=16, weight="bold", color="#0f172a"),
                ft.Container(height=5),
                ft.Container(content=chart, height=220, expand=True)
            ]),
            padding=15,
            border=ft.Border.all(1, "#e2e8f0"),
            border_radius=8,
            expand=True
        )
        
        table_container = ft.Container(
            content=ft.Column([
                ft.Text(f"{comp.split(' ')[0]} — Raw marks", size=16, weight="bold", color="#0f172a"),
                ft.Container(
                    content=ft.DataTable(
                        columns=[
                            ft.DataColumn(ft.Text("Subject", size=11, color="#64748b")),
                            ft.DataColumn(ft.Text(f"Score (/{max_score})", size=11, color="#64748b")),
                        ],
                        rows=raw_rows,
                        column_spacing=20,
                        data_row_min_height=30,
                        data_row_max_height=30,
                    ),
                    border=ft.Border.all(1, "#f1f5f9"),
                    border_radius=8,
                )
            ]),
            padding=15,
            width=280
        )
        
        if failing_subjects:
            warn_bg = "#fef2f2"
            warn_color = "#b91c1c"
            warn_title = "Warning: Below Academic Standard"
            warn_text = f"Academic Alert: Performance in {', '.join(failing_subjects)} is currently below the 60% threshold. Immediate intervention is recommended to prevent future academic failure in these areas."
            icon_value = "⚠️"
        else:
            warn_bg = "#f0fdf4"
            warn_color = "#15803d"
            warn_title = "Satisfactory performance"
            warn_text = f"Among subjects with recorded scores for {comp.split(' ')[0]}, all met or exceeded the 60% standard."
            icon_value = "✅"
            
        warning_container = ft.Container(
            content=ft.Row([
                ft.Text(icon_value, size=24, color=warn_color),
                ft.Container(
                    content=ft.Column([
                        ft.Text(warn_title, size=14, weight="bold", color=warn_color),
                        ft.Text(warn_text, size=12, color="#334155")
                    ], spacing=2),
                    expand=True
                )
            ]),
            padding=12,
            bgcolor=warn_bg,
            border=ft.Border.only(left=ft.BorderSide(4, warn_color)),
            border_radius=ft.border_radius.only(top_right=4, bottom_right=4),
            margin=ft.margin.only(top=10)
        )
        
        # Build Expansion Tile
        exp_tile = ft.ExpansionTile(
            title=ft.Text(f"{comp.split(' ')[0]} (max {max_score})", weight="bold", size=14, color="#0f172a"),
            controls=[
                ft.Container(
                    content=ft.Column([
                        ft.Row([chart_container, table_container], vertical_alignment=ft.CrossAxisAlignment.START, spacing=15),
                        warning_container
                    ]),
                    padding=20,
                    bgcolor="#ffffff",
                    border=ft.Border.only(top=ft.BorderSide(1, "#e2e8f0"))
                )
            ],
            expanded=comp.startswith("Worksheet"), # auto-expand the first one
            collapsed_bgcolor="#ffffff",
            bgcolor="#ffffff",
        )
        
        tiles.append(
            ft.Container(
                content=exp_tile,
                border=ft.Border.all(1, "#cbd5e1"),
                border_radius=8,
                margin=ft.margin.only(bottom=12),
                bgcolor="#ffffff"
            )
        )
        
    return tiles

def build_parent_quarter(page: ft.Page, app_state, quarter: str) -> ft.View:
    """Show marks and analysis for a single quarter for the logged-in parent's student."""

    student_name = (app_state.auth.user_name or "Student").title()
    route = f"/parent/quarter?q={quarter}"

    suffix_map = {"Q1": "1st Quarter", "Q2": "2nd Quarter", "Q3": "3rd Quarter", "Q4": "4th Quarter"}
    quarter_label = suffix_map.get(quarter, quarter)

    controls = []

    # Get data specifically mapped for the detailed table (reproducing Component Level Analytics)
    df_pivot = build_full_component_pivot(student_name, quarter)

    if df_pivot.empty:
        controls.append(ft.Container(
            content=ft.Text(f"{quarter_label} Analysis", size=32, weight="bold"),
            margin=ft.margin.only(bottom=10)
        ))
        controls.append(build_notice(
            "No Data Available",
            "There are currently no grades recorded for this quarter yet.",
            tone="warning"
        ))
        return ft.View(route=route, controls=controls)

    # Check completeness just for the Average Banner
    is_complete = is_quarter_complete_for_student(student_name, quarter)

    import traceback
    df_display = df_pivot.copy()
    try:
        # ── Dashboard Title & Final Average Banner ───────────────────────────
        if is_complete and not df_display["Total Output"].empty:
            avg_score = df_display["Total Output"].mean()
            controls.append(ft.Container(
                content=ft.Row([
                    ft.Text(f"{quarter_label} Overview", size=28, weight="bold", color="#0f172a"),
                    ft.Container(
                        content=ft.Text(f"Quarter Average: {avg_score:.1f}%", size=15, weight="bold", color="#15803d"),
                        bgcolor="#f0fdf4",
                        border=ft.Border.all(1, "#bbf7d0"),
                        padding=ft.padding.symmetric(horizontal=12, vertical=6),
                        border_radius=20
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                margin=ft.margin.only(bottom=24)
            ))
        else:
            controls.append(ft.Container(
                content=ft.Text(f"{quarter_label} Action Matrix (In Progress)", size=24, weight="w600", color="#334155"),
                margin=ft.margin.only(bottom=24)
            ))

        # ── Top Graphical Visualizations ─────────────────────────────────────
        controls.append(
            ft.Row([
                _build_standings_chart(df_display, quarter_label),
                _build_distribution_chart(df_display)
            ], spacing=20, vertical_alignment=ft.CrossAxisAlignment.START)
        )
    
        controls.append(ft.Divider(height=40, color="transparent"))
        
        # ── Performance Badges ───────────────────────────────────────────────
        controls.append(_build_badges_row(df_display))
    
        controls.append(ft.Divider(height=40, color="transparent"))
    
        # ── Component-Level Analytics Engine (Wide Table) ────────────────────
        controls.append(build_section_header("Component-Level Analytics Engine", "Exact numeric grading breakdown per assessment category."))
        
        df_for_table = df_display.copy()
        # Ensure format matches 94.0 precision correctly
        for c in df_for_table.columns:
            if c != "Subject":
                df_for_table[c] = df_for_table[c].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "-")
                
        controls.append(build_data_table(df_for_table))
        
        controls.append(ft.Divider(height=40, color="transparent"))

        # ── Detailed Collapsible Component Analytics ─────────────────────────
        controls.extend(_build_component_expansion_list(df_display))
        
        return ft.View(
            route=route, 
            controls=[ft.Container(
                content=ft.Column(controls, scroll=ft.ScrollMode.AUTO),
                padding=ft.padding.only(left=20, right=20, top=20, bottom=40),
                expand=True
            )],
            scroll=ft.ScrollMode.AUTO
        )
    except Exception as e:
        error_msg = f"Error rendering quarter view:\n{traceback.format_exc()}"
        print(error_msg)
        controls.append(ft.Text(error_msg, color="red"))
        return ft.View(route=route, controls=controls)
