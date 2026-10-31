import json
import dataclasses
from pathlib import Path
from typing import TypeVar, Type

T = TypeVar('T', bound='JsonModel')


@dataclasses.dataclass
class JsonModel:
    """
    Base class for JSON-backed dataclasses.

    Subclasses define their fields as dataclass fields with defaults.
    Provides:
      - load(path)      classmethod, returns default instance if file missing/corrupt
      - to_dict()       serializes to plain dict
      - from_dict(data) classmethod, ignores unknown keys, uses defaults for missing

    Mutable state is stored through DCMStorage. load reads package files.
    """

    @classmethod
    def from_dict(cls: Type[T], data: dict) -> T:
        """
        Create an instance from a dict. Unknown keys are ignored.
        Missing keys use the dataclass default.
        """
        field_names = {f.name for f in dataclasses.fields(cls)}
        filtered = {k: v for k, v in data.items() if k in field_names}
        return cls(**filtered)

    def to_dict(self) -> dict:
        """Serialize to a plain dict."""
        return dataclasses.asdict(self)

    @classmethod
    def load(cls: Type[T], path: Path) -> T:
        """
        Load from a JSON file. Returns a default instance if the
        file does not exist or is corrupt.
        """
        if path.exists():
            try:
                with open(path, 'r') as fp:
                    data = json.load(fp)
                return cls.from_dict(data)
            except (json.JSONDecodeError, KeyError, TypeError):
                return cls()
        return cls()
