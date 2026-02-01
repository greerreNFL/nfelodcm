import dataclasses
from typing import Optional

from .json_model import JsonModel


@dataclasses.dataclass
class TableState(JsonModel):
    """
    Mutable per-table runtime state.
    One file per table at State/tables/{name}.json.
    """
    last_local_update: Optional[str] = None
    last_freshness_check: Optional[str] = None
