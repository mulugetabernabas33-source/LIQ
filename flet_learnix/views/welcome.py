import flet as ft

def build_welcome(page: ft.Page, app_state) -> ft.View:
    dev_cards = ft.Row([
        ft.Container(
            content=ft.Column([
                ft.Text("Jallel.Million", size=22, weight=ft.FontWeight.W_800, color="#1a1a2e"),
                ft.Text("Grade 11 Student at New English Private School", size=15, color="#64748b", text_align=ft.TextAlign.CENTER)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=25, width=280, height=160, bgcolor="#ffffff", border_radius=16,
            border=ft.Border.all(1, "#e2e8f0"),
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.07, "#000000"), offset=ft.Offset(0, 4))
        ),
        ft.Container(
            content=ft.Column([
                ft.Text("Barkot.Daniel", size=22, weight=ft.FontWeight.W_800, color="#1a1a2e"),
                ft.Text("Grade 11 Student at New English Private School", size=15, color="#64748b", text_align=ft.TextAlign.CENTER)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=25, width=280, height=160, bgcolor="#ffffff", border_radius=16,
            border=ft.Border.all(1, "#e2e8f0"),
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.07, "#000000"), offset=ft.Offset(0, 4))
        ),
        ft.Container(
            content=ft.Column([
                ft.Text("Eyeole.Yirga", size=22, weight=ft.FontWeight.W_800, color="#1a1a2e"),
                ft.Text("Grade 11 Student at New English Private School", size=15, color="#64748b", text_align=ft.TextAlign.CENTER)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=25, width=280, height=160, bgcolor="#ffffff", border_radius=16,
            border=ft.Border.all(1, "#e2e8f0"),
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.07, "#000000"), offset=ft.Offset(0, 4))
        ),
        ft.Container(
            content=ft.Column([
                ft.Text("Henos", size=22, weight=ft.FontWeight.W_800, color="#1a1a2e"),
                ft.Text("Grade 11 Student at New English Private School", size=15, color="#64748b", text_align=ft.TextAlign.CENTER)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=25, width=280, height=160, bgcolor="#ffffff", border_radius=16,
            border=ft.Border.all(1, "#e2e8f0"),
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.07, "#000000"), offset=ft.Offset(0, 4))
        ),
    ], wrap=True, alignment=ft.MainAxisAlignment.CENTER)

    about_text = ft.Column([
        ft.Text("About", size=50, weight=ft.FontWeight.W_800, color="#1a1a2e"),
        ft.Text("Transforming Ethiopian Education Through Digital Innovation", size=28, weight=ft.FontWeight.W_800, color="#334155"),
        ft.Text("Ethiopia's education system stands at a pivotal moment. This platform was developed to bring transparency, efficiency, and data-informed decision-making to every level of the country's educational landscape.", size=18, color="#64748b"),
        ft.Container(height=20),
        ft.Text("Development Team", size=22, weight=ft.FontWeight.W_800, color="#1a1a2e"),
        ft.Text("This platform was designed and developed by Ethiopian high school students with a shared commitment to improving the future of education.", size=18, color="#64748b")
    ], width=900)

    hero_section = ft.Container(
        content=ft.Column([
            ft.Image(src="/liq_logo.png", width=120, height=120, fit=ft.ImageFit.CONTAIN),
            ft.Container(height=10),
            ft.Text("WELCOME TO LIQ", size=70, weight=ft.FontWeight.W_900, color="#1a1a2e"),
            ft.Text("Smart Learning Analytics and Early Warning System", size=21, weight=ft.FontWeight.W_500, color="#64748b"),
            ft.Container(height=30),
            ft.ElevatedButton(
                "GET STARTED",
                on_click=lambda e: page.go("/setup/school"),
                style=ft.ButtonStyle(
                    color="#ffffff",
                    bgcolor="#1a1a2e",
                    padding=ft.padding.symmetric(horizontal=50, vertical=20),
                    shape=ft.RoundedRectangleBorder(radius=50),
                    elevation=6,
                )
            ),
            ft.Container(height=100),
            about_text,
            ft.Container(height=100),
            ft.Text("Main Developer", size=50, weight=ft.FontWeight.W_800, color="#1a1a2e"),
            ft.Container(
                content=ft.Column([
                    ft.Text("Bernabas Mulugeta", size=32, weight=ft.FontWeight.W_900, color="#1a1a2e"),
                    ft.Text("Grade 11 Student at New English Private School", size=16, color="#64748b")
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=50, border_radius=20, width=650,
                bgcolor="#ffffff",
                border=ft.Border.all(1, "#e2e8f0"),
                shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.07, "#000000"), offset=ft.Offset(0, 4))
            ),
            ft.Container(height=80),
            ft.Text("Others", size=50, weight=ft.FontWeight.W_800, color="#1a1a2e"),
            dev_cards
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.padding.symmetric(vertical=100, horizontal=20),
        alignment=ft.Alignment(0, 0)
    )

    return ft.View(
        route="/",
        controls=[
            ft.AppBar(
                title=ft.Row([
                    ft.Image(src="/liq_logo.png", width=36, height=36, fit=ft.ImageFit.CONTAIN),
                    ft.Text("LIQ", weight=ft.FontWeight.W_900, size=26, color="#1a1a2e"),
                ], spacing=10),
                bgcolor="#ffffff",
                center_title=False,
                shadow_color=ft.Colors.with_opacity(0.06, "#000000"),
            ),
            ft.Container(
                content=ft.Column(
                    [hero_section],
                    scroll=ft.ScrollMode.AUTO,
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                expand=True,
                bgcolor="#ffffff",
            )
        ],
        padding=0,
        bgcolor="#ffffff"
    )
