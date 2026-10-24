import flet as ft
from views.setup._base import build_setup_layout
from constants import REGIONS
from components.dialogs import show_snack

def build_region(page: ft.Page, app_state) -> ft.View:
    dd = ft.Dropdown(
        options=[ft.dropdown.Option(r) for r in REGIONS],
        value=app_state.selections.region or "Select Region",
        border_radius=8,
        bgcolor="#ffffff",
        color="#0f172a"
    )

    def go_back(e):
        page.go("/")

    def go_next(e):
        if dd.value == "Select Region":
            show_snack(page, "Please select a region.")
            return
        if dd.value != "Addis Ababa":
            show_snack(page, "For this prototype, only 'Addis Ababa' is available.")
            return
        app_state.selections.region = dd.value
        page.go("/setup/kifle-ketema")

    view = build_setup_layout(
        title="Select Region",
        subtitle="Choose your administrative region.",
        chip="School Setup",
        content=dd,
        on_back=go_back,
        on_continue=go_next
    )
    view.route = "/setup/region"
    return view
