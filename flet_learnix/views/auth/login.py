import flet as ft
from views.setup._base import build_setup_layout
from services.db_services import verify_user, log_activity
from constants import TEACHER_CREDENTIALS, PARENT_CREDENTIALS
from components.dialogs import show_snack

def build_login(page: ft.Page, app_state) -> ft.View:
    role_type = app_state.auth.role or "teacher"

    user_input = ft.TextField(
        label="Username" if role_type == "teacher" else "Student Name",
        border_radius=8, bgcolor="#f8fafc",
        border_color="#e2e8f0", focused_border_color="#1a1a2e"
    )
    id_input = ft.TextField(
        label="Teacher ID" if role_type == "teacher" else "Student ID",
        border_radius=8, bgcolor="#f8fafc",
        border_color="#e2e8f0", focused_border_color="#1a1a2e"
    )
    password = ft.TextField(
        label="Password", password=True, can_reveal_password=True,
        border_radius=8, bgcolor="#f8fafc",
        border_color="#e2e8f0", focused_border_color="#1a1a2e"
    )

    def demo_fill(e):
        if role_type == "admin":
            user_input.value = "System Administrator"
            id_input.value = "admin-1"
            password.value = "admin123"
        elif role_type == "teacher":
            user_input.value = "Tafesse"
            id_input.value = "neps-t-4567"
            password.value = "1234"
        else:
            user_input.value = "Jallel Million"
            id_input.value = "neps-s-8903"
            password.value = "1234"
        page.update()

    def go_back(e):
        page.go("/setup/role")

    def perform_login(e):
        if not all([user_input.value, id_input.value, password.value]):
            show_snack(page, "Please fill all required fields.")
            return

        valid = verify_user(username=user_input.value, password=password.value, role=role_type)

        if not valid:
            username_lower = user_input.value.lower()
            if role_type == "teacher":
                cred = TEACHER_CREDENTIALS.get(username_lower, {})
                valid = (username_lower == "tafesse" and id_input.value == cred.get("id") and password.value == cred.get("pass"))
            else:
                cred = PARENT_CREDENTIALS.get(username_lower, {})
                valid = (username_lower == "jallel million" and id_input.value == cred.get("id") and password.value == cred.get("pass"))

        if valid:
            app_state.auth.login(user_input.value, role_type)
            log_activity(user_input.value, "login", role_type, f"Logged in to {role_type} dashboard")
            page.go(f"/{role_type}")
        else:
            show_snack(page, "Invalid credentials.")

    demo_btn = ft.ElevatedButton(
        f"Demo Fill ({role_type.capitalize()})",
        on_click=demo_fill,
        bgcolor="#f1f5f9", color="#1a1a2e",
        elevation=0
    )

    content = ft.Column([
        demo_btn,
        user_input, id_input, password,
        ft.Checkbox(label="Remember Me", fill_color="#1a1a2e")
    ])

    view = build_setup_layout(
        title="Login Form",
        subtitle="Welcome back! Please enter your details.",
        chip="Secure Sign In",
        content=content,
        on_back=go_back,
        on_continue=perform_login
    )
    view.route = "/auth/login"
    return view
