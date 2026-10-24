import flet as ft
from components.banner import build_stat_row
from components.section_header import build_section_header
from components.data_table import build_data_table
from components.dialogs import build_notice
from constants import COMPONENTS, COMPONENT_DISPLAY
from services.analytics import (
    get_student_notes_df
)

def build_parent_notes(page: ft.Page, app_state) -> ft.View:
    student_name = (app_state.auth.user_name or "Student").title()
    df_notes = get_student_notes_df(student_name)
    
    controls = [
        build_section_header("Teacher Notes & Recommendations", f"Chronological observations for {student_name}.")
    ]

    if df_notes.empty:
        controls.append(ft.Text("No recorded notes or concerns for this student.", color="#64748b"))
        return ft.View(route="/parent/notes", controls=controls)

    for _, row in df_notes.iterrows():
        controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text(row["date_recorded"], weight="bold", size=12, color="#475569"),
                    ft.Text(row["note"], size=16, color="#0f172a")
                ]),
                bgcolor="#f8fafc", padding=20, border_radius=12, border=ft.Border.all(1, "#cbd5e1"),
                margin=ft.margin.only(bottom=15)
            )
        )
    
    return ft.View(route="/parent/notes", controls=controls)
