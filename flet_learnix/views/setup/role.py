import flet as ft
from views.setup._base import build_setup_layout

def build_role(page: ft.Page, app_state) -> ft.View:

    def go_dashboard(role_key, route):
        def handler(e):
            if role_key in ["teacher", "parent", "admin"]:
                app_state.auth.login(role_key.capitalize(), role_key)
                if role_key == "teacher":
                    app_state.selections.classroom = "9A"
            page.go(route)
        return handler

    def make_btn(label, icon, role_key, route, color):
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(icon, color="#ffffff", size=22),
                    width=44, height=44, border_radius=11,
                    bgcolor=color,
                    alignment=ft.Alignment(0, 0),
                ),
                ft.Column([
                    ft.Text(label, size=15, weight=ft.FontWeight.W_700, color="#1a1a2e"),
                    ft.Text(f"Go to {label}", size=12, color="#94a3b8"),
                ], spacing=2, expand=True),
                ft.Icon(ft.Icons.ARROW_FORWARD_IOS, color="#cbd5e1", size=16),
            ], spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=16,
            border_radius=14,
            bgcolor="#ffffff",
            border=ft.Border.all(1, "#e2e8f0"),
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.04, "#000000"), offset=ft.Offset(0, 2)),
            on_click=go_dashboard(role_key, route),
            ink=True,
            ink_color="#f1f5f9",
        )

    buttons = ft.Column([
        make_btn("Teacher's Dashboard",      ft.Icons.SCHOOL,                 "teacher",      "/teacher/overview",    "#3b82f6"),
        make_btn("Parent's Dashboard",       ft.Icons.FAMILY_RESTROOM,        "parent",       "/parent/overview",     "#8b5cf6"),
        make_btn("Admin Dashboard",          ft.Icons.ADMIN_PANEL_SETTINGS,   "admin",        "/admin/overview",      "#10b981"),
        make_btn("School Administration",    ft.Icons.BUSINESS,               "school-admin", "/school-admin",        "#f59e0b"),
        make_btn("Wereda Dashboard",         ft.Icons.MAP,                    "wereda",       "/wereda-dash",         "#ef4444"),
        make_btn("Kifle Ketema Dashboard",   ft.Icons.LOCATION_CITY,          "kifle-ketema", "/kifle-ketema-dash",   "#06b6d4"),
        make_btn("Addis Ababa Dashboard",    ft.Icons.ACCOUNT_BALANCE,        "addis-ababa",  "/addis-ababa-dash",    "#ec4899"),
    ], spacing=10)

    def go_back(e):
        page.go("/setup/school")

    view = build_setup_layout(
        title="Choose Dashboard",
        subtitle="Select the dashboard you want to access directly.",
        chip="Access Portal",
        content=buttons,
        on_back=go_back,
        on_continue=None
    )
    view.route = "/setup/role"
    return view
