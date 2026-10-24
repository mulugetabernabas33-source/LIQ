import flet as ft

def build_section_header(title: str, subtitle: str) -> ft.Container:
    """Section header — clean white style."""
    return ft.Container(
        content=ft.Column([
            ft.Text(title, size=26, weight=ft.FontWeight.W_800, color="#1a1a2e"),
            ft.Text(subtitle, size=16, color="#64748b", height=1.65),
        ], spacing=5),
        margin=ft.margin.only(top=28, bottom=16)
    )


def build_notice(title: str, message: str, tone: str = "warning") -> ft.Container:
    """Notice / alert box.
    tone can be 'critical', 'warning', or 'positive'.
    """
    tones = {
        "critical": {"bg": "#fef2f2", "border": "#fca5a5", "text": "#991b1b"},
        "warning":  {"bg": "#fffbeb", "border": "#fde68a", "text": "#854d0e"},
        "positive": {"bg": "#ecfdf5", "border": "#86efac", "text": "#166534"}
    }

    selected_tone = tones.get(tone, tones["warning"])

    return ft.Container(
        content=ft.Column([
            ft.Text(title, weight=ft.FontWeight.BOLD, size=16, color=selected_tone["text"]),
            ft.Text(message, size=15, color=selected_tone["text"])
        ], spacing=5),
        padding=18,
        bgcolor=selected_tone["bg"],
        border=ft.Border.all(1, selected_tone["border"]),
        border_radius=14,
        margin=ft.margin.only(bottom=14),
        shadow=ft.BoxShadow(
            blur_radius=10,
            color=ft.Colors.with_opacity(0.04, "#000000"),
            offset=ft.Offset(0, 2)
        )
    )


def show_snack(page: ft.Page, message: str, tone: str = "error"):
    """Utility snack bar."""
    bgcolor = ft.Colors.RED_700 if tone == "error" else ft.Colors.GREEN_700
    page.snack_bar = ft.SnackBar(ft.Text(message), bgcolor=bgcolor)
    page.snack_bar.open = True
    page.update()
