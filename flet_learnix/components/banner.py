import flet as ft

def build_banner(title: str, subtitle: str, chip_label: str, meta_items: list = None,
                 panel_label: str = None, panel_value: str = None, panel_note: str = None) -> ft.Container:
    """Dashboard banner — clean white card style."""

    meta_row = ft.Row()
    if meta_items:
        meta_row.controls = [
            ft.Container(
                content=ft.Text(item, size=13, weight=ft.FontWeight.BOLD, color="#64748b"),
                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                bgcolor="#f1f5f9",
                border=ft.Border.all(1, "#e2e8f0"),
                border_radius=999,
            ) for item in meta_items
        ]

    left_content = ft.Column([
        ft.Container(
            content=ft.Text(chip_label.upper(), size=12, weight=ft.FontWeight.W_800, color="#1a1a2e"),
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            bgcolor="#f1f5f9",
            border=ft.Border.all(1, "#e2e8f0"),
            border_radius=999,
        ),
        ft.Text(title, size=32, weight=ft.FontWeight.W_900, color="#1a1a2e"),
        ft.Text(subtitle, size=16, color="#64748b"),
        meta_row
    ], spacing=10, expand=True)

    panel_content = None
    if panel_label and panel_value:
        panel_content = ft.Container(
            content=ft.Column([
                ft.Text(panel_label.upper(), size=12, weight=ft.FontWeight.W_700, color="#64748b"),
                ft.Text(panel_value, size=26, weight=ft.FontWeight.W_900, color="#1a1a2e"),
                ft.Text(panel_note or "", size=13, color="#94a3b8")
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=18,
            bgcolor="#f8fafc",
            border=ft.Border.all(1, "#e2e8f0"),
            border_radius=16,
            width=250,
        )

    layout = ft.Row([left_content], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    if panel_content:
        layout.controls.append(panel_content)

    return ft.Container(
        content=layout,
        padding=28,
        margin=ft.margin.only(bottom=22),
        border_radius=20,
        bgcolor="#ffffff",
        border=ft.Border.all(1, "#e2e8f0"),
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=16,
            color=ft.Colors.with_opacity(0.06, "#000000"),
            offset=ft.Offset(0, 4)
        )
    )


def build_stat_card(label: str, value: str, note: str) -> ft.Container:
    """Stat card — white with subtle shadow."""
    return ft.Container(
        content=ft.Column([
            ft.Text(label.upper(), size=13, weight=ft.FontWeight.W_800, color="#64748b"),
            ft.Text(str(value), size=31, weight=ft.FontWeight.W_900, color="#1a1a2e"),
            ft.Text(note, size=15, color="#94a3b8")
        ], spacing=10),
        padding=22,
        bgcolor="#ffffff",
        border=ft.Border.all(1, "#e2e8f0"),
        border_radius=16,
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=10,
            color=ft.Colors.with_opacity(0.04, "#000000"),
            offset=ft.Offset(0, 2)
        ),
        width=220,
    )


def build_stat_row(cards: list) -> ft.Row:
    """Given a list of dicts [{'label':..., 'value':..., 'note':...}], renders a responsive row."""
    rendered = [build_stat_card(c["label"], c["value"], c["note"]) for c in cards]
    return ft.Row(rendered, spacing=16, scroll=ft.ScrollMode.AUTO)
