# nfelo DCM

nfelo DCM is an abstraction layer for loading and caching NFL related CSVs stored on the web. DCM stands for Dataframe-CSV Mapping. The goal of the DCM is to get pandas dataframes of fresh data loaded in a way that balances simplicity, efficiency, and performance.

```python
import nfelodcm

## Load 2 dataframes
db = nfelodcm.load(['pbp', 'games'])

## access the PBP dataframe
db['pbp']
```

## Maps

Maps are config files that tell the DCM where data CSVs are located, how they should be retrieved, and what fields to pull. Each CSV has its own config in `Maps/{table}.json`, where parameters can be set for things like freshness SLAs, CSV parsing engines, iteration strategy, and assignments (mutations).

An important characteristic of these maps is that all fields must be 1) specified in the map and 2) typed. Fields not listed in the map will not be loaded. Untyped fields will throw an error.

Here is a sample config:

```json
{
  "name": "games",
  "description": "nflgamedata games",
  "download_url": "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv",
  "compression": null,
  "engine": "c",
  "freshness": {
    "type": "gh_commit",
    "gh_api_endpoint": "https://api.github.com/repos/nflverse/nfldata/commits",
    "gh_release_tag": null,
    "sla_seconds": 500
  },
  "iter": {
    "type": null,
    "start": null
  },
  "assignments": [
    "fastr_team_id_repl",
    "score_clean"
  ],
  "map": {
    "game_id": "object",
    "season": "int32",
    "week": "int32",
    ...
  }
}
```

### Config Fields

| Field | Description |
|-------|-------------|
| `name` | Table identifier |
| `description` | Human-readable description |
| `download_url` | URL to fetch CSV (use `{0}` placeholder for season in iter tables) |
| `compression` | Compression type (`"gzip"`, `null`) |
| `engine` | Pandas CSV engine (`"c"`, `"python"`) |
| `freshness.type` | `"gh_release"` or `"gh_commit"` |
| `freshness.gh_api_endpoint` | GitHub API endpoint for freshness checks |
| `freshness.gh_release_tag` | Release tag for `gh_release` type |
| `freshness.sla_seconds` | Seconds before re-checking freshness |
| `iter.type` | `"season"` for multi-file tables, `null` for single file |
| `iter.start` | Starting year for season iteration |
| `iter.accept_partial` | Allow success if some season files fail |
| `assignments` | List of assignment function names to apply |
| `map` | Column name → dtype mapping |

## Freshness

The DCM uses a two-tier freshness strategy:

1. **SLA Check**: If the last freshness check was within `sla_seconds`, skip the remote check entirely
2. **Remote Check**: Query GitHub API to compare remote timestamps against local state

For `gh_release` tables, freshness is determined by the `updated_at` timestamp of release assets. For `gh_commit` tables, freshness is based on the latest commit date.

### Per-File Freshness (v0.2.1+)

For season-iterated tables (pbp, rosters, player_stats, etc.), the DCM tracks freshness per-season. When an update is needed, only stale seasons are re-downloaded - cached seasons are read from `Data/Parts/{table}/`. This significantly reduces bandwidth for incremental updates.

## Data Storage

```
Data/
  games.csv
  pbp.csv                # Combined table CSV
  Parts/
    pbp/
      1999.csv           # Per-season cache (iter tables only)
      2000.csv
      ...
State/
  Tables/
    games.json           # Per-table state (last_local_update, last_freshness_check)
    pbp.json
  Parts/
    pbp.json             # Per-season timestamps (iter tables only)
  Global/
    season_state.json    # Current NFL season state
```

## Assignments

Assignments are DataFrame transformations applied after data is pulled. They take a DataFrame as input and return a mutated DataFrame. Assignments are defined in `Engine/Assignments/` and referenced by name in config files.

Common assignments include:
- `fastr_team_id_repl` - Standardize team abbreviations
- `score_clean` - Fix known data errors in game scores
- `penalty_formatting` - Parse penalty descriptions

## GitHub Token (Optional)

To increase GitHub API rate limits from 60/hr to 5,000/hr, create a `.env` file in your working directory:

```
GITHUB_TOKEN=ghp_your_token_here
```

The token is used for freshness checks only, not for downloading CSVs. A token is only relevant/needed when pulling many tables with extremely
fast processing times. In most use cases, the default rate limit is sufficient.

## API

```python
import nfelodcm

# Load tables
db = nfelodcm.load(['pbp', 'games'])

# Get a single DataFrame
df = nfelodcm.get_df('pbp')

# Get table config
config = nfelodcm.get_map('games')

# List available tables
tables = nfelodcm.list_tables()

# Get current season state
season, week = nfelodcm.get_season_state('last_full_week')
```

## Further Detailed Documentation
| File | Description |
|-------|-------------|
| `nfelodcm/Engine/Primatives/README.md` | Core architecture of the DCM data pipeline |
| `tests/README.md` | Test suite for the DCM |
