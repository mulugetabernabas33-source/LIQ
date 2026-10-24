from dataclasses import dataclass, field
from state.auth_state import AuthState
from state.selection_state import SelectionState

@dataclass
class AppState:
    """Central store orchestrating auth and selections across the app.
    Acts as the replacement for the vast st.session_state dictionary.
    """
    auth: AuthState = field(default_factory=AuthState)
    selections: SelectionState = field(default_factory=SelectionState)

    def reset_selections(self):
        """Clears wizard selections if the user returns to the Welcome page."""
        self.selections = SelectionState()
