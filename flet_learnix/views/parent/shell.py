import flet as ft
from services.db_services import log_activity

def build_parent_shell(page: ft.Page, app_state, content_view: ft.View) -> ft.View:
    student_name = (app_state.auth.user_name or "Student").title()
    current_menu = app_state.selections.dashboard_menu_parent

    def on_nav(e):
        menu = e.control.data
        app_state.selections.dashboard_menu_parent = menu
        if menu == "Overview":
            page.go("/parent/overview")
        elif "Quarter" in menu:
            q = menu.split(" ")[0]
            page.go(f"/parent/quarter?q=Q{q[0]}")
        elif menu == "Teacher Notes":
            page.go("/parent/notes")

    def build_nav_btn(label: str, icon: str):
        is_active = current_menu == label
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, color="#8b5cf6" if is_active else "#94a3b8", size=20),
                ft.Text(
                    label,
                    weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.NORMAL,
                    color="#1a1a2e" if is_active else "#64748b",
                    size=14
                )
            ]),
            padding=12,
            border_radius=10,
            bgcolor="#f5f3ff" if is_active else ft.Colors.TRANSPARENT,
            data=label,
            on_click=on_nav,
            ink=True,
            ink_color="#ede9fe"
        )

    def logout(e):
        log_activity(app_state.auth.user_name, "logout", "parent", "Logged out from parent dashboard")
        app_state.auth.logout()
        page.go("/")

    sidebar = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Image(src="/liq_logo.png", width=32, height=32, fit=ft.ImageFit.CONTAIN),
                ft.Text("liq", size=20, weight=ft.FontWeight.W_900, color="#1a1a2e"),
            ], spacing=8),
            ft.Container(height=6),
            ft.Container(
                content=ft.Text("Parent Portal", size=12, weight=ft.FontWeight.W_800, color="#8b5cf6"),
                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                bgcolor="#f5f3ff",
                border=ft.Border.all(1, "#e9d5ff"),
                border_radius=999
            ),
            ft.Container(height=6),
            ft.Text(student_name, size=22, weight=ft.FontWeight.W_900, color="#1a1a2e"),
            ft.Text("Academic monitoring and alerts", size=13, color="#94a3b8"),
            ft.Divider(height=30, color="#e2e8f0"),
            build_nav_btn("Overview",      ft.Icons.DASHBOARD),
            build_nav_btn("1st Quarter",   ft.Icons.INSERT_CHART_OUTLINED),
            build_nav_btn("2nd Quarter",   ft.Icons.INSERT_CHART_OUTLINED),
            build_nav_btn("3rd Quarter",   ft.Icons.INSERT_CHART_OUTLINED),
            build_nav_btn("4th Quarter",   ft.Icons.INSERT_CHART_OUTLINED),
            build_nav_btn("Teacher Notes", ft.Icons.NOTES),
            ft.Container(height=40),
            ft.Divider(height=20, color="#e2e8f0"),
            ft.Text("Signed in as Parent/Guardian", size=12, color="#94a3b8", text_align=ft.TextAlign.CENTER),
            ft.ElevatedButton(
                "Sign Out", on_click=logout,
                bgcolor="#fef2f2", color="#dc2626",
                width=210, elevation=0
            )
        ], spacing=4),
        width=250,
        padding=20,
        bgcolor="#ffffff",
        border=ft.Border.only(right=ft.BorderSide(1, "#e2e8f0"))
    )

    header = ft.Container(
        content=ft.Column([
            ft.Text("Welcome", size=36, weight=ft.FontWeight.W_900, color="#1a1a2e"),
            ft.Text("Here is your child's academic performance overview", size=17, color="#64748b")
        ]),
        border=ft.Border.only(bottom=ft.BorderSide(1, "#e2e8f0")),
        padding=ft.padding.only(bottom=14),
        margin=ft.margin.only(bottom=28)
    )

    return ft.View(
        route=content_view.route,
        controls=[
            ft.Row([
                sidebar,
                ft.Container(
                    content=ft.ListView(
                        controls=[header] + content_view.controls,
                        spacing=0,
                        padding=40,
                    ),
                    expand=True,
                    bgcolor="#ffffff"
                )
            ], expand=True)
        ],
        padding=0,
        bgcolor="#ffffff"
    )
