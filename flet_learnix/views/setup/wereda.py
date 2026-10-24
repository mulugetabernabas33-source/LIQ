import flet as ft
from views.setup._base import build_setup_layout
from constants import WEREDAS
from components.dialogs import show_snack

def build_wereda(page: ft.Page, app_state) -> ft.View:
    dd = ft.Dropdown(
        options=[ft.dropdown.Option(r) for r in WEREDAS],
        value=app_state.selections.wereda or "Select Wereda",
        border_radius=8,
        bgcolor="#ffffff",
        color="#0f172a"
    )

    def go_back(e):
        page.go("/setup/kifle-ketema")

    def go_next(e):
        if dd.value == "Select Wereda":
            show_snack(page, "Please select a Wereda.")
            return
        app_state.selections.wereda = dd.value
        page.go("/setup/school")

    kk_name = app_state.selections.kifle_ketema or "your Kifle Ketema"
    view = build_setup_layout(
        title="Select Wereda",
        subtitle=f"Weredas in {kk_name}.",
        chip="School Setup",
        content=dd,
        on_back=go_back,
        on_continue=go_next
    )
    view.route = "/setup/wereda"
    return view
