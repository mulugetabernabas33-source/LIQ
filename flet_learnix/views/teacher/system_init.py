import flet as ft
from components.banner import build_banner
from components.section_header import build_section_header
from components.data_table import build_data_table
from components.dialogs import show_snack
from services.db_services import get_students, get_subjects, get_db_connection, get_or_create_student, upload_grades_from_excel
from constants import QUARTERS
import os
import pandas as pd

def build_system_init(page: ft.Page, app_state) -> ft.View:
    banner = build_banner(
        "System Initialization & Data Upload",
        "Upload a master Excel file to initialise or refresh the grade database.",
        "ADMIN FUNCTION",
        meta_items=["Supported format: .xlsx", "Requires: student_name, subject, score"]
    )

    upload_mode = ft.RadioGroup(
        content=ft.Row([
            ft.Radio(value="Append", label="Append (keep existing data)"),
            ft.Radio(value="Overwrite", label="Overwrite (clear all data first)")
        ]),
        value="Append"
    )

    # File path text field (replaces FilePicker which is broken in Flet 0.84)
    file_path_field = ft.TextField(
        label="Excel File Path",
        hint_text="Paste the full path to your .xlsx file here (e.g. C:\\Users\\...\\grades.xlsx)",
        expand=True
    )

    def on_upload_click(e):
        fpath = file_path_field.value.strip()
        if not fpath:
            show_snack(page, "Please enter the file path first.")
            return
        if not os.path.exists(fpath):
            show_snack(page, f"File not found: {fpath}")
            return
        if not (fpath.endswith(".xlsx") or fpath.endswith(".xls")):
            show_snack(page, "Only .xlsx or .xls files are supported.")
            return

        clear = (upload_mode.value == "Overwrite")
        success, msg = upload_grades_from_excel(fpath, clear_existing=clear)
        if success:
            show_snack(page, msg, tone="success")
            page.go("/teacher/system-init")
        else:
            show_snack(page, msg)

    students_now = get_students()
    subjects_now = [s for s in get_subjects() if s["name"] != "__TERM_ATT__"]

    s_df = pd.DataFrame(students_now)[["name"]].rename(columns={"name": "Name"}) if students_now else None
    sub_df = pd.DataFrame(subjects_now)[["name"]].rename(columns={"name": "Subject"}) if subjects_now else None

    # Manual setup
    manual_entry = ft.TextField(label="Student Name (e.g. Abebe.Kebede)")
    def add_manual(e):
        if manual_entry.value.strip():
            get_or_create_student(manual_entry.value.strip())
            show_snack(page, f"Student {manual_entry.value} added", tone="success")
            page.go("/teacher/system-init")

    # Danger zone
    def clear_db(e):
        conn = get_db_connection()
        if conn:
            try:
                c = conn.cursor()
                for tbl in ["component_grades", "teacher_notes", "grades", "attendance", "students", "subjects", "terms"]:
                    c.execute(f"DELETE FROM {tbl}")
                conn.commit()
                for q in QUARTERS:
                    c.execute("INSERT OR IGNORE INTO terms (name) VALUES (?)", (q,))
                conn.commit()
                show_snack(page, "Database cleared.", tone="success")
                page.go("/teacher/system-init")
            finally:
                conn.close()

    controls = [
        banner,
        build_section_header("Upload Excel File", "Paste the full file path to your grades spreadsheet below."),
        upload_mode,
        ft.Row([file_path_field, ft.ElevatedButton("Upload", on_click=on_upload_click, bgcolor="#2563eb", color="white")]),
        ft.Divider(),
        build_section_header("Manual Setup", "Add students manually"),
        ft.Row([manual_entry, ft.ElevatedButton("Save Student", on_click=add_manual)]),
        ft.Divider(),
        build_section_header("Current Snapshot", "Live database view"),
        ft.Row([
            ft.Container(content=ft.Column([ft.Text(f"Students ({len(students_now)})", weight="bold"), build_data_table(s_df)]), width=400),
            ft.Container(content=ft.Column([ft.Text(f"Subjects ({len(subjects_now)})", weight="bold"), build_data_table(sub_df)]), width=400)
        ]),
        ft.Divider(),
        ft.ExpansionTile(
            title=ft.Text("Danger Zone — Clear Database", color="#dc2626"),
            controls=[
                ft.Text("Permanently deletes all data."),
                ft.ElevatedButton("Clear Entire Database", on_click=clear_db, bgcolor="#dc2626", color="white")
            ]
        )
    ]

    return ft.View(route="/teacher/system-init", controls=controls)
