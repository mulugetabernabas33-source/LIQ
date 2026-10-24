import flet as ft

def build_teacher_shell(page: ft.Page, app_state, content_view: ft.View) -> ft.View:
    def on_nav(e):
        app_state.selections.dashboard_menu_teacher = e.control.data
        if e.control.data == "Dashboard":
            page.go("/teacher/overview")
        elif "Quarter" in e.control.data:
            page.go(f"/teacher/markbook?q={e.control.data.split(' ')[0]}")
        elif e.control.data == "Teacher Notes":
            page.go("/teacher/notes")
        elif e.control.data == "System Initialization":
            page.go("/teacher/system-init")

    def build_nav_btn(label: str, icon: str):
        is_active = app_state.selections.dashboard_menu_teacher == label
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, color="#1a1a2e" if is_active else "#94a3b8", size=20),
                ft.Text(
                    label,
                    weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.NORMAL,
                    color="#1a1a2e" if is_active else "#64748b",
                    size=14
                )
            ]),
            padding=12,
            border_radius=10,
            bgcolor="#f1f5f9" if is_active else ft.Colors.TRANSPARENT,
            data=label,
            on_click=on_nav,
            ink=True,
        )

    sidebar = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Image(src="/liq_logo.png", width=32, height=32, fit=ft.ImageFit.CONTAIN),
                ft.Text("liq", size=20, weight=ft.FontWeight.W_900, color="#1a1a2e"),
            ], spacing=8),
            ft.Container(height=4),
            ft.Text(
                app_state.selections.school or "SCHOOL",
                size=13, weight=ft.FontWeight.BOLD, color="#64748b"
            ),
            ft.Container(height=16),
            ft.Text("TEACHER WORKSPACE", size=11, weight=ft.FontWeight.BOLD, color="#94a3b8"),
            ft.Container(height=4),
            build_nav_btn("Dashboard",           ft.Icons.DASHBOARD),
            build_nav_btn("1st Quarter",         ft.Icons.EDIT_DOCUMENT),
            build_nav_btn("2nd Quarter",         ft.Icons.EDIT_DOCUMENT),
            build_nav_btn("3rd Quarter",         ft.Icons.EDIT_DOCUMENT),
            build_nav_btn("4th Quarter",         ft.Icons.EDIT_DOCUMENT),
            build_nav_btn("Teacher Notes",       ft.Icons.NOTE),
            build_nav_btn("System Initialization", ft.Icons.SETTINGS),
            ft.Container(height=40),
            ft.ElevatedButton(
                "Log Out",
                on_click=lambda e: page.go("/"),
                bgcolor="#fef2f2",
                color="#dc2626",
                elevation=0
            )
        ], spacing=4),
        width=250,
        padding=20,
        bgcolor="#ffffff",
        border=ft.Border.only(right=ft.BorderSide(1, "#e2e8f0"))
    )

    return ft.View(
        route=content_view.route,
        controls=[
            ft.Row([
                sidebar,
                ft.Container(
                    content=ft.ListView(
                        controls=content_view.controls,
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
