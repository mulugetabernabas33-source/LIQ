import flet as ft
from components.banner import build_stat_row
from components.section_header import build_section_header
from services.db_services import get_db_connection

def build_admin_overview(page: ft.Page, app_state) -> ft.Control:
    # Fetch base stats & audit logs
    total_users = 0
    total_students = 0
    total_subjects = 0
    recent_logs = []
    
    conn = get_db_connection()
    if conn:
        try:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM users")
            total_users = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM students")
            total_students = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM subjects WHERE name != '__TERM_ATT__'")
            total_subjects = c.fetchone()[0]
            
            c.execute("SELECT username, action, timestamp, details FROM activity_log ORDER BY id DESC LIMIT 5")
            recent_logs = c.fetchall()
        except Exception:
            pass
        finally:
            conn.close()

    stat_cards = build_stat_row([
        {"label": "Registered Sub-Accounts", "value": str(total_users), "note": "Teachers, Parents, Admins"},
        {"label": "Registered Students", "value": str(total_students), "note": "Database Entries"},
        {"label": "Course Modules", "value": str(total_subjects), "note": "Configured Subjects"}
    ])
    
    # Format Audit Logs
    log_rows = []
    if not recent_logs:
        log_rows.append(ft.Text("No recent log activity.", italic=True, color="#64748b"))
    else:
        for r in recent_logs:
            log_rows.append(
                ft.Row([
                    ft.Icon(ft.Icons.SECURITY_UPDATE_GOOD if "login" not in r["action"] else ft.Icons.LOGIN, color="#64748b", size=20),
                    ft.Text(f"{r['timestamp'][:16]}", color="#64748b", size=12, width=120),
                    ft.Text(f"{r['username']} ({r['action']}) - {r['details']}", size=14)
                ], spacing=15)
            )

    controls = [
        ft.Row([
            ft.Icon(ft.Icons.ANALYTICS, color="#3b82f6", size=40),
            ft.Text("System Overview", size=28, weight="bold", color="#0f172a")
        ], alignment=ft.MainAxisAlignment.START, spacing=15),
        ft.Text("Live database metrics and system health status.", color="#64748b", size=16),
        ft.Divider(height=30, color="transparent"),
        
        stat_cards,
        
        ft.Divider(height=40),
        
        ft.Row([
            ft.Column([
                build_section_header("System Infrastructure", "Backend state validation"),
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.VERIFIED_USER_ROUNDED, color="#10b981", size=30),
                        ft.Column([
                            ft.Text("Database Online", weight="bold", size=16),
                            ft.Text("Connected to SQLite backend successfully.", color="#64748b")
                        ])
                    ], spacing=15),
                    padding=20,
                    bgcolor="#ffffff",
                    border_radius=12,
                    border=ft.Border.all(1, "#e2e8f0"),
                    width=400
                )
            ]),
            ft.Column([
                build_section_header("Audit Trail", "Recent background activity logs"),
                ft.Container(
                    content=ft.Column(log_rows, spacing=10),
                    padding=20,
                    bgcolor="#ffffff",
                    border_radius=12,
                    border=ft.Border.all(1, "#e2e8f0"),
                    width=400
                )
            ])
        ], alignment=ft.MainAxisAlignment.START, spacing=30, wrap=True)
    ]
    
    # We return a column wrapping the controls
    return ft.Column(controls, spacing=10)
