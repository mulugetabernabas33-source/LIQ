import flet as ft
import pandas as pd
import flet_charts as fc

def build_bar_chart(df: pd.DataFrame, x_col: str, y_col: str) -> ft.Container:
    """Builds a Flet native BarChart from a Pandas DataFrame replacing px.bar."""
    if df is None or df.empty:
        return ft.Container(ft.Text("No chart data available"))

    max_y = df[y_col].max()
    max_y = max_y if pd.notna(max_y) and max_y > 0 else 100
    
    chart_groups = []
    for i, (_, row) in enumerate(df.iterrows()):
        val = row[y_col]
        if pd.isna(val):
            val = 0
            
        chart_groups.append(
            fc.BarChartGroup(
                x=i,
                rods=[
                    fc.BarChartRod(
                        from_y=0,
                        to_y=val,
                        width=28,
                        color="#38bdf8",
                        tooltip=f"{row[x_col]}\n{val:.1f}",
                        border_radius=4,
                    )
                ]
            )
        )
        
    chart = fc.BarChart(
        groups=chart_groups,
        border=ft.Border.all(1, "#cbd5e1"),
        left_axis=fc.ChartAxis(label_size=40, title=ft.Text(y_col)),
        bottom_axis=fc.ChartAxis(
            labels=[
                fc.ChartAxisLabel(
                    value=i, 
                    label=ft.Container(ft.Text(str(row[x_col])[:10], size=10), padding=5)
                )
                for i, (_, row) in enumerate(df.iterrows())
            ],
            label_size=40,
        ),
        horizontal_grid_lines=fc.ChartGridLines(
            color="#e2e8f0", width=1, dash_pattern=[3, 3]
        ),
        
        max_y=max_y * 1.1,
        interactive=True,
    )
    
    return ft.Container(
        content=chart,
        height=300,
        padding=20,
        bgcolor="#ffffff",
        border_radius=12,
        border=ft.Border.all(1, "#e2e8f0")
    )

def build_line_chart(df: pd.DataFrame, x_col: str, y_col: str) -> ft.Container:
    """Builds a Flet native LineChart from a Pandas DataFrame replacing px.line."""
    if df is None or df.empty:
        return ft.Container(ft.Text("No chart data available"))

    max_y = df[y_col].max()
    max_y = max_y if pd.notna(max_y) and max_y > 0 else 100

    data_points = []
    for i, (_, row) in enumerate(df.iterrows()):
        val = row[y_col]
        if pd.isna(val):
            continue
        data_points.append(
            fc.LineChartDataPoint(i, val)
        )

    chart = fc.LineChart(
        data_series=[
            fc.LineChartData(
                points=data_points,
                stroke_width=4,
                color="#0f4c81",
                curved=True,
                rounded_stroke_cap=True,
                point=True,
            )
        ],
        border=ft.Border.all(1, "#cbd5e1"),
        left_axis=fc.ChartAxis(label_size=40, title=ft.Text(y_col)),
        bottom_axis=fc.ChartAxis(
            labels=[
                fc.ChartAxisLabel(
                    value=i, 
                    label=ft.Container(ft.Text(str(row[x_col])[:10], size=10), padding=5)
                )
                for i, (_, row) in enumerate(df.iterrows())
            ],
            label_size=40,
        ),
        horizontal_grid_lines=fc.ChartGridLines(
            color="#e2e8f0", width=1, dash_pattern=[3, 3]
        ),
        
        max_y=max_y * 1.1,
        min_y=0,
        interactive=True,
    )

    return ft.Container(
        content=chart,
        height=300,
        padding=20,
        bgcolor="#ffffff",
        border_radius=12,
        border=ft.Border.all(1, "#e2e8f0")
    )
