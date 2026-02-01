import dataclasses
from typing import Optional

from .json_model import JsonModel


@dataclasses.dataclass
class SeasonState(JsonModel):
    """
    Global season state.
    Single file at State/global/season_state.json.
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
