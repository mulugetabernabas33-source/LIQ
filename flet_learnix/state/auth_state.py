from dataclasses import dataclass
from typing import Optional

@dataclass
class AuthState:
    """Manages user authentication session.
    Replacement for st.session_state['logged_in'] and st.session_state['user_name']
    """
    is_logged_in: bool = False
    is_admin_logged_in: bool = False
    user_name: Optional[str] = None
    admin_user: Optional[str] = None
    role: Optional[str] = None # e.g. "teacher", "parent", "admin"

    def login(self, username: str, role: str):
        self.is_logged_in = True
        self.user_name = username
        self.role = role

    def admin_login(self, admin_user: str):
        self.is_admin_logged_in = True
        self.admin_user = admin_user
        self.role = "admin"

    def logout(self):
        self.is_logged_in = False
        self.is_admin_logged_in = False
        self.user_name = None
        self.admin_user = None
        self.role = None
