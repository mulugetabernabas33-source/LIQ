import flet as ft
from components.dialogs import show_snack
from services.db_services import (
    get_db_connection,
    toggle_user_status,
    delete_user,
    reset_user_pwd,
    log_activity,
    register_user,
)


def _open_dialog(page: ft.Page, dialog: ft.AlertDialog):
    """Open a dialog safely using page.overlay (works in all Flet versions)."""
    dialog.open = True
    if dialog not in page.overlay:
        page.overlay.append(dialog)
    page.update()


def _close_dialog(page: ft.Page, dialog: ft.AlertDialog):
    """Close the dialog and remove from overlay."""
    dialog.open = False
    page.update()


def build_admin_accounts(page: ft.Page, app_state) -> ft.Control:

    container = ft.Column(spacing=20)

    def load_users():
        container.controls.clear()

        users_data = []
        conn = get_db_connection()
        if conn:
            try:
                c = conn.cursor()
                c.execute("SELECT id, username, role, COALESCE(is_disabled, 0) as is_disabled FROM users")
                users_data = c.fetchall()
            except Exception as e:
                print(e)
            finally:
                conn.close()

        if not users_data:
            container.controls.append(ft.Text("No user accounts found.", italic=True))
            return

        rows = []
        for u in users_data:
            uid = u["id"]
            uname = u["username"]
            role = str(u["role"]).upper()
            is_disabled = bool(u["is_disabled"])

            status_color = "#ef4444" if is_disabled else "#10b981"
            status_text = "Disabled" if is_disabled else "Active"

            def make_toggle_handler(user_id, current_val, name):
                def handler(e):
                    new_val = 0 if current_val else 1
                    if toggle_user_status(user_id, new_val):
                        log_activity(app_state.auth.user_name, "toggle_status", "admin",
                                     f"{'Disabled' if new_val else 'Enabled'} account {name}")
                        show_snack(page, "Account status updated.", tone="success")
                        refresh_ui()
                return handler

            def make_delete_handler(user_id, name):
                def handler(e):
                    dlg = ft.AlertDialog(modal=True)

                    def confirm_delete(ec):
                        if delete_user(user_id):
                            log_activity(app_state.auth.user_name, "delete_user", "admin", f"Deleted account {name}")
                            show_snack(page, "User deleted permanently.", tone="success")
                        _close_dialog(page, dlg)
                        refresh_ui()

                    dlg.title = ft.Text("Confirm Deletion")
                    dlg.content = ft.Text(f"Permanently delete account '{name}'?")
                    dlg.actions = [
                        ft.TextButton("Cancel", on_click=lambda _: _close_dialog(page, dlg)),
                        ft.ElevatedButton("Delete", color="#ffffff", bgcolor="#ef4444", on_click=confirm_delete),
                    ]
                    _open_dialog(page, dlg)
                return handler

            def make_reset_handler(user_id, name):
                def handler(e):
                    pwd_field = ft.TextField(label="New Password", password=True)
                    dlg = ft.AlertDialog(modal=True)

                    def confirm_reset(ec):
                        if not pwd_field.value:
                            show_snack(page, "Password cannot be empty.")
                            return
                        if reset_user_pwd(user_id, pwd_field.value):
                            log_activity(app_state.auth.user_name, "pwd_reset", "admin", f"Reset password for {name}")
                            show_snack(page, "Password reset successfully.", tone="success")
                        _close_dialog(page, dlg)

                    dlg.title = ft.Text(f"Reset Password for {name}")
                    dlg.content = pwd_field
                    dlg.actions = [
                        ft.TextButton("Cancel", on_click=lambda _: _close_dialog(page, dlg)),
                        ft.ElevatedButton("Reset", on_click=confirm_reset),
                    ]
                    _open_dialog(page, dlg)
                return handler

            row = ft.Container(
                content=ft.Row([
                    ft.Row([
                        ft.CircleAvatar(content=ft.Icon(ft.Icons.PERSON)),
                        ft.Column([
                            ft.Text(uname, weight="bold"),
                            ft.Text(role, color="#64748b", size=12)
                        ], spacing=0)
                    ], width=200),
                    ft.Container(
                        content=ft.Text(status_text, size=12, color=status_color, weight="bold"),
                        bgcolor=f"{status_color}22",
                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                        border_radius=12,
                        width=100
                    ),
                    ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.LOCK if not is_disabled else ft.Icons.LOCK_OPEN,
                            icon_color="#f59e0b",
                            tooltip="Toggle Account Status",
                            on_click=make_toggle_handler(uid, is_disabled, uname)
                        ),
                        ft.IconButton(
                            icon=ft.Icons.PASSWORD_ROUNDED,
                            icon_color="#3b82f6",
                            tooltip="Reset Password",
                            on_click=make_reset_handler(uid, uname)
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_FOREVER,
                            icon_color="#ef4444",
                            tooltip="Delete Account",
                            on_click=make_delete_handler(uid, uname)
                        )
                    ], spacing=0)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=15,
                border=ft.Border(bottom=ft.BorderSide(1, "#f1f5f9"))
            )
            rows.append(row)

        container.controls.extend(rows)

    def refresh_ui():
        load_users()
        page.update()

    def show_add_user_dialog(e):
        uname_field = ft.TextField(label="Username")
        role_drop = ft.Dropdown(label="Role", options=[
            ft.dropdown.Option("teacher"),
            ft.dropdown.Option("parent"),
        ])
        pwd_field = ft.TextField(label="Password", password=True)
        dlg = ft.AlertDialog(modal=True)

        def attempt_register(ec):
            if not uname_field.value or not role_drop.value or not pwd_field.value:
                show_snack(page, "All fields are required.")
                return
            success, msg = register_user(uname_field.value, pwd_field.value, role_drop.value)
            if success:
                log_activity(app_state.auth.user_name, "create_user", "admin",
                             f"Created {role_drop.value} account: {uname_field.value}")
                show_snack(page, "User created successfully!", tone="success")
                _close_dialog(page, dlg)
                refresh_ui()
            else:
                show_snack(page, msg)

        dlg.title = ft.Text("Add New User")
        dlg.content = ft.Column([uname_field, role_drop, pwd_field], tight=True, width=300)
        dlg.actions = [
            ft.TextButton("Cancel", on_click=lambda _: _close_dialog(page, dlg)),
            ft.ElevatedButton("Create", on_click=attempt_register, bgcolor="#10b981", color="white"),
        ]
        _open_dialog(page, dlg)

    load_users()

    return ft.Column([
        ft.Row([
            ft.Row([
                ft.Icon(ft.Icons.MANAGE_ACCOUNTS, color="#3b82f6", size=40),
                ft.Text("Account Management", size=28, weight="bold", color="#0f172a")
            ], spacing=15),
            ft.ElevatedButton(
                "Add User",
                icon=ft.Icons.ADD,
                bgcolor="#3b82f6",
                color="white",
                on_click=show_add_user_dialog
            )
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Text("Administrate system access, modify credentials, and manage active roles.",
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
