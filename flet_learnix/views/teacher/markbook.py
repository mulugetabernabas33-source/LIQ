import flet as ft
from components.banner import build_banner, build_stat_row
from components.section_header import build_section_header
from services.db_services import (
    get_students, get_subjects, get_or_create_student,
    get_or_create_term, get_term_row, get_student_row, get_subject_row,
     save_student_attendance
)
from services.analytics import save_component_scores, build_student_markbook_df, compute_student_totals
from components.dialogs import show_snack
from constants import COMPONENTS, ALL_ROWS, ATTENDANCE_ROW

def build_teacher_markbook(page: ft.Page, app_state, quarter: str) -> ft.View:
    teacher_name = app_state.auth.user_name or "Teacher"
    classroom = app_state.selections.classroom

    db_students = [s["name"] for s in get_students()]
    db_subjects = [s["name"] for s in get_subjects() if s["name"] != "__TERM_ATT__"]

    banner = build_banner(
        f"{quarter} Markbook",
        f"Review and update marks for Class {classroom}.",
        "QUARTER CODE",
        meta_items=[f"Teacher: {teacher_name}", f"Students: {len(db_students)}", "Scores and attendance"],
        panel_label="Quarter Code",
        panel_value=quarter,
        panel_note="Expand student to edit"
    )

    stats = build_stat_row([
        {"label": "Students", "value": str(len(db_students)), "note": "Enrolled"},
        {"label": "Subjects", "value": str(len(db_subjects)), "note": "In system"},
        {"label": "Components", "value": str(len(COMPONENTS)), "note": "Scored per subject"},
        {"label": "Attendance Codes", "value": "P / A / L", "note": "Present, Absent, Late"}
    ])

    controls = [banner, stats]

    if not db_students:
        controls.append(ft.Text("No students found. Add a student below."))
        
        new_s_field = ft.TextField(label="Student name (e.g. Abebe.Kebede)")
        def add_student(e):
            if new_s_field.value.strip():
                get_or_create_student(new_s_field.value.strip())
                page.go(f"/teacher/markbook?q={quarter}")
        controls.append(ft.Row([new_s_field, ft.ElevatedButton("Add Student", on_click=add_student)]))
        return ft.View(route=f"/teacher/markbook", controls=controls)

    if not db_subjects:
        controls.append(ft.Text("No subjects found. Please use System Initialization to configure."))
        return ft.View(route=f"/teacher/markbook", controls=controls)

    term_row = get_term_row(quarter)
    if not term_row:
        get_or_create_term(quarter)
        term_row = get_term_row(quarter)

    term_id = term_row["id"]
    
    controls.append(build_section_header("Entry Guidance", "Expand a student to edit marks. Save after editing."))

    # Build the custom "Datagrid"
    student_tiles = []
    for student_name in db_students:
        s_row = get_student_row(student_name)
        if not s_row: continue
        student_id = s_row["id"]

        df_raw = build_student_markbook_df(student_id, term_id, db_subjects)
        
        # State refs for this student's inputs
        inputs_map = {} # { (component, subject): TextField }
        
        # Create table header
        header_cells = [ft.Container(ft.Text("Component", weight="bold", size=11, color="#64748b"), width=130)]
        for subj in db_subjects:
            header_cells.append(ft.Container(ft.Text(subj[:10], weight="bold", size=11, color="#64748b"), width=60))
        header_row = ft.Row(header_cells, scroll=ft.ScrollMode.AUTO)
        
        table_rows = [header_row, ft.Divider()]

        for comp in ALL_ROWS:
            cells = [ft.Container(ft.Text(comp, size=12, color="#0f172a"), width=130)]
            for subj in db_subjects:
                val = df_raw.at[comp, subj]
                tf = ft.TextField(
                    value=str(val) if str(val) not in ["nan", "None", "-"] else "",
                    width=60, height=35, text_size=12,
                    content_padding=ft.padding.all(5)
                )
                inputs_map[(comp, subj)] = tf
                cells.append(tf)
            table_rows.append(ft.Row(cells, scroll=ft.ScrollMode.AUTO))

        def make_save_handler(sid, smap, sname):
            def on_save(e):
                for subj in db_subjects:
                    sub_row = get_subject_row(subj)
                    if not sub_row: continue
                    subj_id = sub_row["id"]

                    comp_scores = {}
                    for c in COMPONENTS:
                        comp_scores[c] = smap[(c, subj)].value
                    
                    save_component_scores(sid, subj_id, term_id, comp_scores)
                
                # Fetch attendance from the first subject's row equivalent since attendance is global
                att_input = smap[(ATTENDANCE_ROW, db_subjects[0])].value
                save_student_attendance(sid, term_id, att_input)
                show_snack(page, f"Saved marks for {sname}!", tone="success")
            return on_save

        save_btn = ft.ElevatedButton(
            f"Save {student_name.replace('.', ' ')}", 
            on_click=make_save_handler(student_id, inputs_map, student_name),
            bgcolor="#10b981", color="white"
        )

        student_tiles.append(
            ft.ExpansionTile(
                title=ft.Text(student_name.replace(".", " "), weight="bold"),
                controls=[
                    ft.Container(
                        content=ft.Column(table_rows + [ft.Container(height=10), save_btn]),
                        padding=10, bgcolor="#f8fafc", border_radius=8
                    )
                ]
            )
        )

    controls.extend(student_tiles)
    return ft.View(route=f"/teacher/markbook", controls=controls)
