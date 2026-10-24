import flet as ft
from components.dialogs import show_snack
from services.db_services import (
    get_db_connection,
    get_or_create_subject,
    edit_subject,
    delete_subject_ext,
    log_activity,
)


def _open_dialog(page: ft.Page, dialog: ft.AlertDialog):
    """Open a dialog safely using page.overlay."""
    dialog.open = True
    if dialog not in page.overlay:
        page.overlay.append(dialog)
    page.update()


def _close_dialog(page: ft.Page, dialog: ft.AlertDialog):
    """Close the dialog."""
    dialog.open = False
    page.update()


def build_admin_subjects(page: ft.Page, app_state) -> ft.Control:

    container = ft.Column(spacing=20)

    def load_subjects():
        container.controls.clear()

        subjects_data = []
        conn = get_db_connection()
        if conn:
            try:
                c = conn.cursor()
                c.execute("SELECT id, name FROM subjects WHERE name != '__TERM_ATT__'")
                subjects_data = c.fetchall()
            except Exception:
                pass
            finally:
                conn.close()

        if not subjects_data:
            container.controls.append(ft.Text("No subjects found in system.", italic=True))
            return

        rows = []
        for s in subjects_data:
            sid = s["id"]
            sname = s["name"]

            def make_edit_handler(subject_id, subject_name):
                def handler(e):
                    name_field = ft.TextField(label="Subject Name", value=subject_name)
                    dlg = ft.AlertDialog(modal=True)

                    def confirm_edit(ec):
                        if not name_field.value:
                            return
                        if edit_subject(subject_id, name_field.value):
                            log_activity(app_state.auth.user_name, "edit_subject", "admin",
                                         f"Renamed {subject_name} to {name_field.value}")
                            show_snack(page, "Subject renamed successfully.", tone="success")
                            _close_dialog(page, dlg)
                            refresh_ui()
                        else:
                            show_snack(page, "Error: Subject name might already exist.")

                    dlg.title = ft.Text("Edit Subject")
                    dlg.content = name_field
                    dlg.actions = [
                        ft.TextButton("Cancel", on_click=lambda _: _close_dialog(page, dlg)),
                        ft.ElevatedButton("Save", on_click=confirm_edit),
                    ]
                    _open_dialog(page, dlg)
                return handler

            def make_delete_handler(subject_id, subject_name):
                def handler(e):
                    dlg = ft.AlertDialog(modal=True)

                    def confirm_delete(ec):
                        if delete_subject_ext(subject_id):
                            log_activity(app_state.auth.user_name, "delete_subject", "admin",
                                         f"Deleted subject {subject_name}")
                            show_snack(page, "Subject deleted.", tone="success")
                        _close_dialog(page, dlg)
                        refresh_ui()

                    dlg.title = ft.Text("Confirm Deletion")
                    dlg.content = ft.Text(
                        f"Are you sure you want to delete '{subject_name}'?\nThis may affect associated grades.")
                    dlg.actions = [
                        ft.TextButton("Cancel", on_click=lambda _: _close_dialog(page, dlg)),
                        ft.ElevatedButton("Delete", color="#ffffff", bgcolor="#ef4444", on_click=confirm_delete),
                    ]
                    _open_dialog(page, dlg)
                return handler

            row = ft.Container(
                content=ft.Row([
                    ft.Row([
                        ft.CircleAvatar(content=ft.Icon(ft.Icons.BOOK), bgcolor="#e0f2fe"),
                        ft.Text(sname, weight="bold", size=16),
                    ], width=250),
                    ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.EDIT,
                            icon_color="#3b82f6",
                            tooltip="Rename Subject",
                            on_click=make_edit_handler(sid, sname)
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_color="#ef4444",
                            tooltip="Delete Subject",
                            on_click=make_delete_handler(sid, sname)
                        )
                    ], spacing=0)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=15,
                border=ft.Border(bottom=ft.BorderSide(1, "#f1f5f9"))
            )
            rows.append(row)

        container.controls.extend(rows)

    def refresh_ui():
        load_subjects()
        page.update()

    def show_add_subject_dialog(e):
        name_field = ft.TextField(label="Subject Name", width=300)
        dlg = ft.AlertDialog(modal=True)

        def attempt_add(ec):
            if not name_field.value:
                show_snack(page, "Subject name cannot be empty.")
                return
            sub = get_or_create_subject(name_field.value)
            if sub:
                log_activity(app_state.auth.user_name, "create_subject", "admin",
                             f"Created subject {name_field.value}")
                show_snack(page, "Subject added successfully!", tone="success")
                _close_dialog(page, dlg)
                refresh_ui()
            else:
                show_snack(page, "Failed to create subject.")

        dlg.title = ft.Text("Add New Subject")
        dlg.content = name_field
        dlg.actions = [
            ft.TextButton("Cancel", on_click=lambda _: _close_dialog(page, dlg)),
            ft.ElevatedButton("Create", on_click=attempt_add, bgcolor="#10b981", color="white"),
        ]
        _open_dialog(page, dlg)

    load_subjects()

    return ft.Column([
        ft.Row([
            ft.Row([
                ft.Icon(ft.Icons.LIBRARY_BOOKS_ROUNDED, color="#3b82f6", size=40),
                ft.Text("Subject Management", size=28, weight="bold", color="#0f172a")
            ], spacing=15),
            ft.ElevatedButton(
                "Add Subject",
                icon=ft.Icons.ADD,
                bgcolor="#3b82f6",
                color="white",
                on_click=show_add_subject_dialog
            )
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Text("Create, modify, and manage the academic courses available for grading.",
                color="#64748b", size=16),
        ft.Divider(height=20, color="transparent"),
        ft.Container(
            content=container,
            bgcolor="#ffffff",
            border_radius=12,
            border=ft.Border.all(1, "#e2e8f0"),
            padding=10
        )
    ], spacing=10)
