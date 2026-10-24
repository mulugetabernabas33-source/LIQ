import flet as ft
from views.setup._base import build_setup_layout
from constants import KIFLE_KETEMAS
from components.dialogs import show_snack

def build_kifle_ketema(page: ft.Page, app_state) -> ft.View:
    dd = ft.Dropdown(
        options=[ft.dropdown.Option(r) for r in KIFLE_KETEMAS],
        value=app_state.selections.kifle_ketema or "Select Kifle Ketema",
        border_radius=8,
        bgcolor="#ffffff",
        color="#0f172a"
    )

    def go_back(e):
        page.go("/setup/region")

    def go_next(e):
        if dd.value == "Select Kifle Ketema":
            show_snack(page, "Please select a Kifle Ketema.")
            return
        app_state.selections.kifle_ketema = dd.value
        page.go("/setup/wereda")

    region_name = app_state.selections.region or "your region"
    view = build_setup_layout(
        title="Select Kifle Ketema",
        subtitle=f"Kifle Ketemas in {region_name}.",
        chip="School Setup",
        content=dd,
        on_back=go_back,
        on_continue=go_next
    )
    view.route = "/setup/kifle-ketema"
    return view
