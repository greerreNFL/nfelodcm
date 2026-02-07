import dataclasses
from typing import Dict, Optional

from .json_model import JsonModel


@dataclasses.dataclass
class IterState(JsonModel):
    """
    Tracks per-season timestamps for iterated tables.
    Keys are string representations of season years for JSON compatibility.
    Values are ISO timestamps of the last known remote update for that season file.
    """
    season_timestamps: Dict[str, Optional[str]] = dataclasses.field(default_factory=dict)

    def get_season_timestamp(self, season):
        """
        Returns the stored timestamp for a season, or None if not tracked
        """
        return self.season_timestamps.get(str(season))

    def set_season_timestamp(self, season, timestamp):
        """
        Sets the timestamp for a season
        """
        self.season_timestamps[str(season)] = timestamp
