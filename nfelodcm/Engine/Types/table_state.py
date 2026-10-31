import dataclasses
from typing import Optional

from .json_model import JsonModel


@dataclasses.dataclass
class TableState(JsonModel):
    """
    Mutable per-table runtime state.
    One file per table at State/Tables/{name}.json in the configured storage.
    """
    last_local_update: Optional[str] = None
    last_freshness_check: Optional[str] = None
