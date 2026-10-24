import flet as ft
import pandas as pd
import importlib

def run_flet_app(page: ft.Page):
    """Main Application Router managing state and views."""
    page.title = "liq"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.bgcolor = "#ffffff"

    from state.app_state import AppState
    from services.db_services import app_init_db

    app_init_db()
    app_state = AppState()

    def _build_home_view() -> ft.View:
        """Build home view with validation."""
        from views.welcome import build_welcome
        home_view = build_welcome(page, app_state)
        if not isinstance(home_view, ft.View):
            raise TypeError("build_welcome() must return ft.View")
        if not getattr(home_view, "route", None):
            home_view.route = "/"
        return home_view

    def _show_fallback_direct(message: str = "Home screen loaded.") -> None:
        """Direct fallback render (no routing/View dependency)."""
        page.clean()
        page.add(
            ft.Container(
                expand=True,
                alignment=ft.Alignment(0, 0),
                bgcolor="#ffffff",
                content=ft.Column(
                    [
                        ft.Image(src="/liq_logo.png", width=80, height=80, fit=ft.ImageFit.CONTAIN),
                        ft.Text("liq", size=34, weight=ft.FontWeight.BOLD, color="#1a1a2e"),
                        ft.Text(message, size=16, color="#64748b"),
                        ft.ElevatedButton("Reload Home", on_click=lambda e: page.go("/")),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=14,
                ),
            )
        )
        page.update()

    def _fallback_view(message: str = "Home screen loaded.") -> ft.View:
        """Safe default view so desktop app never opens blank."""
        return ft.View(
            route="/",
            controls=[
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment(0, 0),
                    bgcolor="#ffffff",
                    content=ft.Column(
                        [
                            ft.Image(src="/liq_logo.png", width=80, height=80, fit=ft.ImageFit.CONTAIN),
                            ft.Text("liq", size=34, weight=ft.FontWeight.BOLD, color="#1a1a2e"),
                            ft.Text(message, size=16, color="#64748b"),
                            ft.ElevatedButton("Reload Home", on_click=lambda e: page.go("/")),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=14,
                    ),
                )
            ],
            padding=20,
            bgcolor="#ffffff"
        )

    def route_change(e):
        print(f"[route_change] route={page.route}")
        page.views.clear()
        try:
            # Public Views
            if page.route == "/":
                page.views.append(_build_home_view())

            # Setup Views — region / kifle-ketema / wereda removed
            elif page.route == "/setup/school":
                from views.setup.school import build_school
                page.views.append(build_school(page, app_state))
            elif page.route == "/setup/role":
                from views.setup.role import build_role
                page.views.append(build_role(page, app_state))

            # Auth Views (kept for compatibility, not in main flow)
            elif page.route.startswith("/auth/register"):
                from views.auth.register import build_register
                page.views.append(build_register(page, app_state))
            elif page.route == "/auth/login":
                from views.auth.login import build_login
                page.views.append(build_login(page, app_state))
            elif page.route == "/auth/classroom":
                from views.auth.classroom import build_classroom
                page.views.append(build_classroom(page, app_state))

            # Teacher Shell — auth guard removed for direct access
            elif page.route.startswith("/teacher"):
                from views.teacher.shell import build_teacher_shell
                if page.route == "/teacher/overview":
                    from views.teacher.overview import build_teacher_overview
                    content = build_teacher_overview(page, app_state)
                elif page.route.startswith("/teacher/markbook"):
                    from views.teacher.markbook import build_teacher_markbook
                    q = page.route.split("?q=")[-1] if "?q=" in page.route else "1st"
                    q = q if q.endswith("Q") else f"Q{q[0]}"
                    content = build_teacher_markbook(page, app_state, q)
                elif page.route == "/teacher/notes":
                    from views.teacher.notes import build_teacher_notes
                    content = build_teacher_notes(page, app_state)
                elif page.route == "/teacher/system-init":
                    from views.teacher.system_init import build_system_init
                    content = build_system_init(page, app_state)
                else:
                    from views.teacher.overview import build_teacher_overview
                    content = build_teacher_overview(page, app_state)
                page.views.append(build_teacher_shell(page, app_state, content))

            # Parent Shell — auth guard removed for direct access
            elif page.route.startswith("/parent"):
                from views.parent.shell import build_parent_shell
                if page.route == "/parent/overview":
                    from views.parent.overview import build_parent_overview
                    content = build_parent_overview(page, app_state)
                elif page.route == "/parent/notes":
                    from views.parent.notes import build_parent_notes
                    content = build_parent_notes(page, app_state)
                elif page.route.startswith("/parent/quarter"):
                    from views.parent.quarter import build_parent_quarter
                    q = page.route.split("?q=")[-1] if "?q=" in page.route else "Q1"
                    content = build_parent_quarter(page, app_state, q)
                else:
                    from views.parent.overview import build_parent_overview
                    content = build_parent_overview(page, app_state)
                page.views.append(build_parent_shell(page, app_state, content))

            # Admin Shell — auth guard removed for direct access
            elif page.route.startswith("/admin"):
                from views.admin.shell import build_admin_shell
                if page.route == "/admin/overview":
                    from views.admin.overview import build_admin_overview
                    content = build_admin_overview(page, app_state)
                elif page.route == "/admin/accounts":
                    from views.admin.accounts import build_admin_accounts
                    content = build_admin_accounts(page, app_state)
                elif page.route == "/admin/subjects":
                    from views.admin.subjects import build_admin_subjects
                    content = build_admin_subjects(page, app_state)
                else:
                    from views.admin.overview import build_admin_overview
                    content = build_admin_overview(page, app_state)
                page.views.append(build_admin_shell(page, app_state, content))

            elif page.route in ["/school-admin", "/wereda-dash", "/kifle-ketema-dash", "/addis-ababa-dash"]:
                page.views.append(ft.View(
                    route=page.route,
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Image(src="/liq_logo.png", width=60, height=60, fit=ft.ImageFit.CONTAIN),
                                ft.Text(f"Route: {page.route}", size=20, weight="bold", color="#1a1a2e"),
                                ft.Text(
                                    "This dashboard links to a separate module. Full port coming soon.",
                                    color="#64748b"
                                ),
                                ft.ElevatedButton("Go back Home", on_click=lambda e: page.go("/"),
                                                  bgcolor="#1a1a2e", color="#ffffff")
                            ], alignment=ft.MainAxisAlignment.CENTER,
                               horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=16),
                            expand=True,
                            alignment=ft.Alignment(0, 0),
                            bgcolor="#ffffff"
                        )
                    ],
                    padding=50,
                    bgcolor="#ffffff"
                ))
            else:
                page.views.append(_fallback_view(f"Unknown route '{page.route}'. Loaded safe home view."))

        except Exception as err:
            print(f"[route_change] ERROR: {err}")
            page.views.clear()
            try:
                page.views.append(_fallback_view(f"Startup fallback loaded due to route error: {err}"))
            except Exception as fallback_err:
                print(f"[route_change] FALLBACK VIEW ERROR: {fallback_err}")
                _show_fallback_direct(f"Startup fallback rendered directly due to route error: {err}")
                return

        if not page.views:
            _show_fallback_direct("No views were added by router. Loaded safe home view.")
            return
        print(f"[route_change] views={len(page.views)} top={page.views[-1].route if page.views else 'none'}")
        page.update()

    def view_pop(e):
        if not page.views:
            _show_fallback_direct("No previous view found. Loaded safe home view.")
            return
        page.views.pop()
        if not page.views:
            _show_fallback_direct("View stack became empty. Loaded safe home view.")
            return
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    print("[startup] Initializing liq UI")
    _show_fallback_direct("Initializing application...")

    try:
        startup_view = _build_home_view()
        page.views.clear()
        page.views.append(startup_view)
        page.route = startup_view.route or "/"
        print(f"[startup] direct home view route={page.route}")
        page.update()
    except Exception as startup_err:
        print(f"[startup] direct home view failed: {startup_err}")
        _show_fallback_direct(f"Home view failed to load: {startup_err}")
        return

    route_change(None)

if __name__ == "__main__":
    ft.app(target=run_flet_app, view=ft.AppView.WEB_BROWSER)
