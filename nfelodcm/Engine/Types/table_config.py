import dataclasses
from typing import Optional, List, Dict, Tuple, Type, TypeVar

from .json_model import JsonModel

T = TypeVar('T', bound='TableConfig')


@dataclasses.dataclass
class IterConfig:
    """
    Iteration configuration for tables that require looping
    through seasons (or similar) to pull data.
    """
    type: Optional[str] = None
    start: Optional[int] = None
    accept_partial: bool = False


@dataclasses.dataclass
class FreshnessConfig:
    """
    Freshness configuration for determining when a table's
    data needs to be re-downloaded.
    """
    type: str = ''
    sla_seconds: int = 900
    gh_api_endpoint: str = ''
    gh_release_tag: Optional[str] = None


@dataclasses.dataclass
class TableConfig(JsonModel):
    """
    Typed configuration for a DCM table. Loaded from Maps/*.json files.
    Replaces raw dict access with attribute access and provides
    validation via validate().
    """
    name: str = ''
    description: str = ''
    download_url: str = ''
    compression: Optional[str] = None
    engine: Optional[str] = 'c'
    iter: IterConfig = dataclasses.field(default_factory=IterConfig)
    freshness: FreshnessConfig = dataclasses.field(default_factory=FreshnessConfig)
    assignments: List[str] = dataclasses.field(default_factory=list)
    map: Dict[str, str] = dataclasses.field(default_factory=dict)

    ## allowed dtypes for map values ##
    ALLOWED_DTYPES = [
        'object', 'int32', 'int64', 'float32', 'float64',
        'boolean', 'interval', 'category', 'datetime64[ns, <tz>]', 'bool'
    ]

    ## validation requirements for top-level fields ##
    _CONFIG_REQUIREMENTS = {
        'name' : {'type': str, 'nullable': False},
        'description' : {'type': str, 'nullable': False},
        'download_url' : {'type': str, 'nullable': False},
        'compression' : {'type': str, 'nullable': True},
        'engine' : {'type': str, 'nullable': True},
        'iter' : {'type': IterConfig, 'nullable': False},
        'assignments' : {'type': list, 'nullable': False},
        'map' : {'type': dict, 'nullable': False},
    }

    def validate(self) -> Tuple[bool, List[dict]]:
        """
        Validates structure and map dtypes. Replaces check_struc + check_map_type.
        Returns a tuple of (passing, errors).
        """
        passing = True
        errors = []
        ## validate structure ##
        for k, v in self._CONFIG_REQUIREMENTS.items():
            val = getattr(self, k)
            if val is None and not v['nullable']:
                passing = False
                errors.append({
                    'type' : 'config_structure',
                    'error_msg' : '{0} is cannot be null'.format(k)
                })
            elif val is not None:
                if not isinstance(val, v['type']):
                    passing = False
                    errors.append({
                        'type' : 'config_structure',
                        'error_msg' : '{0} must be a {1}'.format(k, v['type'])
                    })
        ## validate map dtypes ##
        for k, v in self.map.items():
            if v not in self.ALLOWED_DTYPES:
                passing = False
                errors.append({
                    'error_type' : 'dtype',
                    'error_msg' : '{0} type provided for {1} is not an accepted datatype'.format(v, k)
                })
        ## return ##
        return passing, errors

    @classmethod
    def from_dict(cls: Type[T], data: dict) -> T:
        """
        Override to handle nested IterConfig and FreshnessConfig.
        Unknown keys are ignored. Missing keys use defaults.
        """
        ## handle nested iter ##
        iter_data = data.get('iter', {})
        if isinstance(iter_data, dict):
            iter_config = IterConfig(
                type=iter_data.get('type'),
                start=iter_data.get('start'),
                accept_partial=iter_data.get('accept_partial', False)
            )
        else:
            iter_config = IterConfig()
        ## handle nested freshness ##
        freshness_data = data.get('freshness', {})
        if isinstance(freshness_data, dict):
            freshness_config = FreshnessConfig(
                type=freshness_data.get('type', ''),
                sla_seconds=freshness_data.get('sla_seconds', 900),
                gh_api_endpoint=freshness_data.get('gh_api_endpoint', ''),
                gh_release_tag=freshness_data.get('gh_release_tag')
            )
        else:
            freshness_config = FreshnessConfig()
        ## build top-level fields ##
        return cls(
            name=data.get('name', ''),
            description=data.get('description', ''),
            download_url=data.get('download_url', ''),
            compression=data.get('compression'),
            engine=data.get('engine', 'c'),
            iter=iter_config,
            freshness=freshness_config,
            assignments=data.get('assignments', []),
            map=data.get('map', {})
        )

    def to_dict(self) -> dict:
        """Serialize to a plain dict, including nested configs."""
        return {
            'name': self.name,
            'description': self.description,
            'download_url': self.download_url,
            'compression': self.compression,
            'engine': self.engine,
            'iter': dataclasses.asdict(self.iter),
            'freshness': dataclasses.asdict(self.freshness),
            'assignments': self.assignments,
            'map': self.map,
        }
