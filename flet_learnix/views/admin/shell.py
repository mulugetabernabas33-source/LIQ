import flet as ft
from components.dialogs import show_snack

def build_admin_shell(page: ft.Page, app_state, content: ft.Control) -> ft.View:
    nav_links = [
        {"icon": ft.Icons.DASHBOARD_ROUNDED,    "label": "Overview",  "route": "/admin/overview"},
        {"icon": ft.Icons.PEOPLE_ALT_ROUNDED,   "label": "Accounts",  "route": "/admin/accounts"},
        {"icon": ft.Icons.LIBRARY_BOOKS_ROUNDED,"label": "Subjects",  "route": "/admin/subjects"},
    ]

    sidebar_controls = [
        ft.Container(
            content=ft.Row([
                ft.Image(src="/liq_logo.png", width=32, height=32, fit=ft.ImageFit.CONTAIN),
                ft.Text("liq", size=20, weight=ft.FontWeight.W_900, color="#1a1a2e")
            ], spacing=8),
            padding=ft.padding.only(bottom=4)
        ),
        ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.SHIELD, color="#10b981", size=18),
                ft.Text("Admin Workspace", size=13, weight="bold", color="#1a1a2e")
            ]),
            padding=ft.padding.only(bottom=16)
        )
    ]

    for link in nav_links:
        is_active = page.route.startswith(link["route"])
        sidebar_controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Icon(link["icon"], color="#10b981" if is_active else "#94a3b8", size=20),
                    ft.Text(
                        link["label"],
                        color="#1a1a2e" if is_active else "#64748b",
                        weight="w600" if is_active else "w400",
                        size=14
                    )
                ]),
                padding=12,
                border_radius=10,
                bgcolor="#ecfdf5" if is_active else ft.Colors.TRANSPARENT,
                on_click=lambda e, r=link["route"]: page.go(r),
                ink=True,
                ink_color="#d1fae5"
            )
        )

    def logout(e):
        app_state.auth.logout()
        page.go("/")

    sidebar_controls.extend([
        ft.Container(expand=True),
        ft.Divider(color="#e2e8f0"),
        ft.ListTile(
            leading=ft.Icon(ft.Icons.LOGOUT, color="#ef4444"),
            title=ft.Text("Logout", color="#ef4444", weight="bold"),
            on_click=logout
        )
    ])

    main_layout = ft.Row([
        ft.Container(
            content=ft.Column(sidebar_controls, expand=True),
            width=250,
            bgcolor="#ffffff",
            padding=20,
            border=ft.Border(right=ft.BorderSide(1, "#e2e8f0")),
        ),
        ft.Container(
            content=ft.ListView(
                controls=[
                    ft.Container(
                        content=ft.Row([
                            ft.Text("System Administration Panel", size=24, weight="bold", color="#1a1a2e"),
                            ft.Container(
                                content=ft.Row([
                                    ft.Icon(ft.Icons.ACCOUNT_CIRCLE, color="#64748b"),
                                    ft.Text(
                                        app_state.auth.user_name.title() if app_state.auth.user_name else "Admin",
                                        weight="bold", color="#1a1a2e"
                                    )
                                ]),
                                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                                bgcolor="#f1f5f9",
                                border_radius=20
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=ft.padding.only(bottom=20)
                    ),
                    content
                ],
                expand=True,
                padding=30,
                spacing=20
            ),
            expand=True,
            bgcolor="#ffffff"
        )
    ], expand=True)

    return ft.View(route=page.route, controls=[main_layout], padding=0, bgcolor="#ffffff")
