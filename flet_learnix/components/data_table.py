import flet as ft
import pandas as pd
import numpy as np

def build_data_table(df: pd.DataFrame, expand: bool = False) -> ft.Container:
    """Safely converts a Pandas DataFrame into a Flet DataTable."""
    if df is None or df.empty:
        return ft.Container(ft.Text("No data available", color="#64748b"), padding=20)

    # Sanitize dataframe
    df = df.replace({np.nan: "-", float('inf'): "-", float('-inf'): "-"})
    
    columns = [
        ft.DataColumn(ft.Text(col, weight=ft.FontWeight.BOLD, color="#0f172a"))
        for col in df.columns
    ]
    
    rows = []
    for _, row in df.iterrows():
        cells = []
        for col in df.columns:
            val = row[col]
            if isinstance(val, float):
                # Format float safely
                try:
                    str_val = f"{val:.1f}" if val != "-" else "-"
                except Exception:
                    str_val = str(val)
            else:
                str_val = str(val)
            cells.append(ft.DataCell(ft.Text(str_val[:50], color="#334155")))
        rows.append(ft.DataRow(cells=cells))

    table = ft.DataTable(
        columns=columns,
        rows=rows,
        border=ft.Border.all(1, "#cbd5e1"),
        border_radius=10,
        heading_row_color="#f8fafc",
        data_row_color={"hovered": "#f1f5f9"}
    )
    
    return ft.Container(
        content=ft.Column([table], scroll=ft.ScrollMode.AUTO, expand=expand),
        expand=expand,
    )
