from dataclasses import dataclass
from typing import Optional

@dataclass
class SelectionState:
    """Manages user form selections (wizard + dashboards).
    Replacement for st.session_state['selected_region'], ['selected_classroom'], etc.
    """
    region: Optional[str] = None
    kifle_ketema: Optional[str] = None
    wereda: Optional[str] = None
    school: Optional[str] = None
    classroom: str = "11A"
    is_homeroom: bool = False
    dashboard_menu_teacher: str = "Dashboard"
    dashboard_menu_parent: str = "Overview"
