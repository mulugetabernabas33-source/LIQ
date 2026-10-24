import flet as ft
from views.setup._base import build_setup_layout
from constants import CLASSROOMS

def build_classroom(page: ft.Page, app_state) -> ft.View:
    dd = ft.Dropdown(
        options=[ft.dropdown.Option(r) for r in CLASSROOMS],
        value=app_state.selections.classroom,
        border_radius=8,
        bgcolor="#f8fafc",
        color="#1a1a2e"
    )

    def go_back(e):
        page.go("/auth/register")

    def go_next(e):
        app_state.selections.classroom = dd.value
        page.go("/auth/login")

    view = build_setup_layout(
        title="Classroom Selection",
        subtitle="Please select the classroom you are assigned to.",
        chip="Teacher Setup",
        content=dd,
        on_back=go_back,
        on_continue=go_next
    )
    view.route = "/auth/classroom"
    return view
