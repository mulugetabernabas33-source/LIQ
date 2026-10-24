import flet as ft
import pandas as pd
from components.banner import build_banner
from components.section_header import build_section_header
from components.dialogs import build_notice, show_snack
from services.db_services import get_students, get_db_connection, get_student_row

def build_teacher_notes(page: ft.Page, app_state) -> ft.View:
    classroom = app_state.selections.classroom
    students_list = [s["name"] for s in get_students()]

    conn = get_db_connection()
    df_notes = (
        pd.read_sql_query(
            """
            SELECT s.name AS Student, t.note, t.date_recorded
            FROM teacher_notes t
            JOIN students s ON t.student_id = s.id
            ORDER BY t.date_recorded DESC
            """, conn
        ) if conn else pd.DataFrame()
    )
    if conn: conn.close()

    banner = build_banner(
        "Teacher Notes and Concerns",
        f"Record staff-only observations for Class {classroom}.",
        "STAFF NOTES",
        panel_label="Recorded Entries",
        panel_value=str(len(df_notes))
    )

    student_dd = ft.Dropdown(
        options=[ft.dropdown.Option(s) for s in students_list],
        label="Select Student"
    )
    note_box = ft.TextField(label="Note / Concern", multiline=True, width=500, height=140)

    def save_note(e):
        if not student_dd.value or not note_box.value.strip():
            show_snack(page, "Please select student and write a note.")
            return
        
        s_row = get_student_row(student_dd.value)
        if s_row:
            cx = get_db_connection()
            try:
                c = cx.cursor()
                c.execute("INSERT INTO teacher_notes (student_id, note) VALUES (?, ?)", (s_row["id"], note_box.value.strip()))
                cx.commit()
                show_snack(page, "Note saved successfully.", tone="success")
                page.go("/teacher/notes") # refresh
            finally:
                cx.close()

    form_col = ft.Column([
        build_section_header("Create New Note", "Capture observations."),
        student_dd,
        note_box,
        ft.ElevatedButton("Save Note", on_click=save_note, bgcolor="#1d4ed8", color="white", disabled=not students_list)
    ])

    status_col = ft.Column([
        build_section_header("Staff Guidance", "Keep entries short and factual."),
        build_notice("Existing Notes", f"{len(df_notes)} notes found." if len(df_notes) > 0 else "No notes yet", tone="positive")
    ])

    display_col = ft.Column([build_section_header("Logged Notes", "Review saved notes.")])
    
    if not df_notes.empty:
        for s in df_notes["Student"].unique():
            s_notes = df_notes[df_notes["Student"] == s]
            note_tiles = []
            for _, r in s_notes.iterrows():
                note_tiles.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(r["date_recorded"], weight="bold", size=12, color="#475569"),
                            ft.Text(r["note"])
                        ]),
                        bgcolor="#f1f5f9", padding=10, border_radius=6, margin=ft.margin.only(bottom=5)
                    )
                )
            display_col.controls.append(
                ft.ExpansionTile(
                    title=ft.Text(f"{s} ({len(s_notes)} notes)"),
                    controls=note_tiles
                )
            )
    else:
        display_col.controls.append(ft.Text("No saved notes found.", color="#64748b"))

    controls = [
        banner,
        ft.Row([ft.Container(content=form_col, expand=3), ft.Container(content=status_col, expand=2)], vertical_alignment=ft.CrossAxisAlignment.START),
        ft.Divider(height=40),
        display_col
    ]

    return ft.View(route="/teacher/notes", controls=controls)
