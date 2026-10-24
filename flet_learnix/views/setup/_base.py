import flet as ft

def build_setup_layout(title: str, subtitle: str, chip: str, content: ft.Control,
                       on_back=None, on_continue=None) -> ft.Container:
    """Replaces render_form_header and shared layout wrappers for setup/auth flow."""
    c_btn = ft.ElevatedButton("Continue", on_click=on_continue, style=ft.ButtonStyle(
        color="#ffffff", bgcolor="#1a1a2e", padding=ft.padding.all(20),
        shape=ft.RoundedRectangleBorder(radius=10), elevation=4,
    )) if on_continue else ft.Container()

    b_btn = ft.ElevatedButton("Back", on_click=on_back, style=ft.ButtonStyle(
        color="#64748b", bgcolor="#f1f5f9", padding=ft.padding.all(20),
        shape=ft.RoundedRectangleBorder(radius=10), elevation=0,
    )) if on_back else ft.Container()

    header = ft.Column([
        ft.Container(
            content=ft.Text(chip.upper(), size=12, weight=ft.FontWeight.W_700, color="#1a1a2e"),
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            bgcolor="#f1f5f9",
            border=ft.Border.all(1, "#e2e8f0"),
            border_radius=999,
        ),
        ft.Text(title, size=30, weight=ft.FontWeight.W_800, color="#1a1a2e"),
        ft.Text(subtitle, size=14, color="#64748b")
    ], spacing=8)

    btn_row_controls = []
    if on_back:
        btn_row_controls.append(b_btn)
    if on_continue:
        btn_row_controls.append(c_btn)

    return ft.View(
        route=None,
        controls=[
            ft.AppBar(
                title=ft.Row([
                    ft.Image(src="/liq_logo.png", width=32, height=32, fit=ft.ImageFit.CONTAIN),
                    ft.Text("LIQ", weight=ft.FontWeight.W_900, size=22, color="#1a1a2e"),
                ], spacing=8),
                bgcolor="#ffffff",
                center_title=False,
                shadow_color=ft.Colors.with_opacity(0.06, "#000000"),
            ),
            ft.Container(
                content=ft.Column([
                    header,
                    ft.Container(height=24),
                    content,
                    ft.Container(height=24),
                    ft.Row(btn_row_controls, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ]),
                width=680,
                padding=44,
                border_radius=20,
                bgcolor="#ffffff",
                border=ft.Border.all(1, "#e2e8f0"),
                shadow=ft.BoxShadow(blur_radius=40, color=ft.Colors.with_opacity(0.08, "#000000"), offset=ft.Offset(0, 8)),
                margin=ft.margin.symmetric(vertical=40, horizontal=20)
            )
        ],
        bgcolor="#f8fafc",
        scroll=ft.ScrollMode.AUTO,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )
