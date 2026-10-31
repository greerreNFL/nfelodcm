import dataclasses
from typing import Optional

from .json_model import JsonModel


@dataclasses.dataclass
class SeasonState(JsonModel):
    """
    Global season state.
    Single file at State/Global/season_state.json in the configured storage.
    last_updated is the UTC ISO timestamp of the calculation, or None when
    the state was inferred rather than calculated.
    """
    last_full_week: Optional[dict] = dataclasses.field(
        default_factory=lambda: {"season": None, "week": None}
    )
    last_partial_week: Optional[dict] = dataclasses.field(
        default_factory=lambda: {"season": None, "week": None}
    )
    next_week: Optional[dict] = dataclasses.field(
        default_factory=lambda: {"season": None, "week": None}
    )
    last_updated: Optional[str] = None

    def week_states(self):
        """
        Returns the week states by name, without last_updated
        """
        return {
            'last_full_week': self.last_full_week,
            'last_partial_week': self.last_partial_week,
            'next_week': self.next_week,
        }
