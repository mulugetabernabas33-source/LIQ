import flet as ft
from views.setup._base import build_setup_layout
from services.db_services import register_user
from components.dialogs import show_snack

def build_register(page: ft.Page, app_state) -> ft.View:
    role_type = app_state.auth.role or "teacher"
    title_str = f"{role_type.capitalize()} Registration"

    def _tf(label):
        return ft.TextField(
            label=label, border_radius=8,
            bgcolor="#f8fafc", border_color="#e2e8f0",
            focused_border_color="#1a1a2e"
        )

    fname    = _tf("First Name")
    lname    = _tf("Last Name")
    email    = _tf("Email Address")
    address  = _tf("Address")
    user_id  = _tf("Teacher ID" if role_type == "teacher" else "User ID")
    password = ft.TextField(
        label="Password", password=True, can_reveal_password=True,
        border_radius=8, bgcolor="#f8fafc",
        border_color="#e2e8f0", focused_border_color="#1a1a2e"
    )
    cpassword = ft.TextField(
        label="Confirm Password", password=True, can_reveal_password=True,
        border_radius=8, bgcolor="#f8fafc",
        border_color="#e2e8f0", focused_border_color="#1a1a2e"
    )

    def demo_fill(e):
        if role_type == "admin":
            fname.value, lname.value = "System", "Administrator"
            email.value = "admin@liq.edu"
            address.value = "Local"
            user_id.value = "admin-1"
            password.value, cpassword.value = "admin123", "admin123"
        elif role_type == "teacher":
            fname.value, lname.value = "Tafesse", "Tamirat"
            email.value = "tafessetamirat@gmail.com"
            address.value = "Ayer Tena"
            user_id.value = "neps-t-4567"
            password.value, cpassword.value = "1234", "1234"
        else:
            fname.value, lname.value = "Jallel", "Million"
            email.value = "jallel.million@example.com"
            address.value = "Addis Ababa"
            user_id.value = "neps-s-8903"
            password.value, cpassword.value = "1234", "1234"
        page.update()

    def go_back(e):
        page.go("/setup/role")

    def create_account(e):
        if not all([fname.value, lname.value, email.value, address.value, user_id.value, password.value, cpassword.value]):
            show_snack(page, "Please fill all fields.")
            return
        if password.value != cpassword.value:
            show_snack(page, "Passwords do not match.")
            return

        success, msg = register_user(
            username=f"{fname.value} {lname.value}".strip(),
            password=password.value,
            role=role_type,
            user_id_code=user_id.value
        )
        if success:
            show_snack(page, msg, tone="success")
            page.go("/auth/classroom" if role_type == "teacher" else "/auth/login")
        else:
            show_snack(page, msg)

    demo_btn = ft.ElevatedButton(
        f"Demo Fill ({role_type.capitalize()})",
        on_click=demo_fill,
        bgcolor="#f1f5f9", color="#1a1a2e", elevation=0
    )

    content = ft.Column([
        demo_btn,
        ft.Row([fname, lname]),
        email, address, user_id,
        ft.Row([password, cpassword])
    ])

    view = build_setup_layout(
        title=title_str,
        subtitle="Not a registered user? Create an account below.",
        chip="Create Account",
        content=content,
        on_back=go_back,
        on_continue=create_account
    )
    view.route = "/auth/register"
    return view
