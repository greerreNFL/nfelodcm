# nfelo DCM

nfelo DCM is an abstraction layer for loading and saving NFL related CSVs stored on the web. DCM stands for Dataframe-CSV Mapping. The goal of the DCM is to get pandas dataframes of fresh data loaded in a way that balances simplicity, efficiency, and performance.

```python
import nfelodcm
import pandas as pd

## Load 2 dataframes
db = nfelodcm.load(['pbp', 'games'])
## access the PBP dataframe ##
db['pbp']

```

## Maps
Maps are config files that tell the dcm, where data CSVs are located, how they should be retrieved, and what fields to pull. Each CSV has its own config, where parameters can be set for things like freshness SLAs, CSV parsing engines, assignments (aka mutations).

An important characteristic of these maps, and overall framework, is that all fields must be 1) specified in the map and 2) typed. Fields not listed in the map will not be loaded. Fields untyped will throw an error.

Here is a sample config:

```javascript
{
  "name": "games",
  "description": "nflgamedata games",
  "last_local_update": "2023-12-16T22:42:41.040569",
  "download_url": "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv",
  "compression": null,
  "engine": "c",
  "freshness": {
    "type": "gh_commit",
    "gh_api_endpoint": "https://api.github.com/repos/nflverse/nfldata/commits",
    "gh_release_tag": null,
    "sla_seconds": null
  },
  "iter": {
    "type": null,
    "start": null
  },
  "assignments": [
    "game_id_repl"
  ],
  "map": {
    "game_id": "object",
    "season": "int32",
    "game_type": "object",
    "week": "int32",
    "gameday": "object",
    "weekday": "object",
    "gametime": "object",
    "away_team": "object",
    "away_score": "float32",
    "home_team": "object",
    "home_score": "float32",
    "location": "object",
    "result": "float32",
    "total": "float32",
    "overtime": "float32",
    "old_game_id": "float32",
    "gsis": "float32",
    "nfl_detail_id": "object",
    "pfr": "object",
    "pff": "float32",
    "espn": "int32",
    "ftn": "float32",
    "away_rest": "int32",
    "home_rest": "int32",
    "away_moneyline": "float32",
    "home_moneyline": "float32",
    "spread_line": "float32",
    "away_spread_odds": "float32",
    "home_spread_odds": "float32",
    "total_line": "float32",
    "under_odds": "float32",
    "over_odds": "float32",
    "div_game": "int32",
    "roof": "object",
    "surface": "object",
    "temp": "float32",
    "wind": "float32",
    "away_qb_id": "object",
    "home_qb_id": "object",
    "away_qb_name": "object",
    "home_qb_name": "object",
    "away_coach": "object",
    "home_coach": "object",
    "referee": "object",
    "stadium_id": "object",
    "stadium": "object"
  }
}
```

## Data
When a CSV is translated into a Dataframe, a copy of the data is stored locally for cached retrieval based on SLAs and freshness. For data stored in github, freshness is determined by either the last release or last commit.
Presently, data is stored locally as CSVs

## Assignments
Assignment is the pandas vernacular for mutate. In the DCM, "Assignments" reference functions that take a dataframe as an input and returns a mutated/assigned dataframe as its response. Assignments can be added to the assignments folder and referenced by name in config files.

## Retrieval
To load data, pass an array of table names to the .load() function. The name passed for each table should match the name of the map file (ie passing 'pbp' would retrieve whatever data was specified in the 'pbp.json')
When this function is called, all freshness checks, caching, downloading, field typing, and mutations are handled automatically behind the scenes.