import flet as ft
from views.setup._base import build_setup_layout
from constants import SCHOOLS, SCHOOL_IMAGE_MAP
from components.dialogs import show_snack

def build_school(page: ft.Page, app_state) -> ft.View:

    def select_school(school_name):
        app_state.selections.school = school_name
        page.go("/setup/role")

    known_schools = [s for s in SCHOOLS if s != "Select School"]

    cards = []
    for school in known_schools:
        img_src = SCHOOL_IMAGE_MAP.get(school.upper(), "")

        content_items = []
        if img_src:
            content_items.append(ft.Image(src=img_src, height=40, fit=ft.BoxFit.CONTAIN))
        else:
            content_items.append(ft.Icon(ft.Icons.ACCOUNT_BALANCE, size=30, color="#94a3b8"))

        content_items.append(
            ft.Text(school, size=14, weight=ft.FontWeight.W_700, color="#1a1a2e", text_align=ft.TextAlign.CENTER)
        )

        card = ft.Container(
            content=ft.Column(
                content_items,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=15,
            border_radius=12,
            bgcolor="#ffffff",
            border=ft.Border.all(1, "#e2e8f0"),
            on_click=lambda e, s=school: select_school(s),
            shadow=ft.BoxShadow(blur_radius=12, color=ft.Colors.with_opacity(0.06, "#000000"), offset=ft.Offset(0, 4)),
            ink=True,
        )
        cards.append(card)

    grid = ft.GridView(
        expand=1,
        runs_count=4,
        max_extent=150,
        child_aspect_ratio=1.0,
        spacing=15,
        run_spacing=15,
        controls=cards
    )

    def go_back(e):
        page.go("/")

    view = build_setup_layout(
        title="Select School",
        subtitle="Choose your school to continue.",
        chip="School Setup",
        content=ft.Container(content=grid, height=400),
        on_back=go_back,
        on_continue=None
    )
    view.route = "/setup/school"
    return view
