# Changelog

## v0.2.1
#### Features
- **GitHub Token Support**: Load `GITHUB_TOKEN` from `.env` file for authenticated API requests, increasing rate limits from 60/hr to 5,000/hr
- **Per-File Iterative Pulls**: Season-based tables (pbp, rosters, player_stats, etc.) now cache individual season files in `Data/Parts/`. Incremental updates only re-download stale seasons instead of all files, with staleness based on per file release timestamps
- **Improved Retry Logic**: Shared retry utility with exponential backoff and error classification. 4xx errors fail fast without retry; 5xx and connection errors retry with backoff, ensuring more resilient data retrieval

#### Architecture
- `DataPull` refactored to atomic unit (single URL → DataFrame)
- New `PullManager` orchestrates iteration, per-file caching, concatenation, and assignments
- New `IterState` type tracks per-season timestamps for selective freshness checks
- `Freshness` now computes `stale_parts` list for `gh_release` iter tables via single API call

#### Dependencies
- Added `python-dotenv>=1.0` for github token support

---

## v0.2.0
#### Features
- Split local state tracking from the map to its own json so pulling new versions does not override local state and pushes to repo do not create difs on the maps.
- json data structures used throughout the package (maps, state, etc) are now IO'd via typed dataclasses
- [DEV] Added pytest-based test suite covering types, config validation, freshness SLA logic, Maps integrity, assignments, and public API
- Added changelog

---

## v0.1.24
#### Patch
- Updating player stats maps to support new fastR pipelines

---

## v0.1.23
#### Patch
- Updating name standardization between QB Elo and fastR datasets

---

## v0.1.22
#### Features
- accept_partials added as a boolean flag for iteration based datasets, allowing the dataset to warn but not fail if some files in the iteration range could not be pulled (ie nflfastR participation data)

#### Patch
- Added new fields to fastR naming check (draft_team, draft_club)
- Updating mapping and col handling on temp_players_handle() to align with the new version of nflfastRs data pulling. Source columns have changed, though the resulting DF columns remain the same as a result of the mapping
- New maps for season player stats, rolling stadium stats

---

## v0.1.21
#### Patch
- Adding CLV calculations as fields for nfelo_games

---

## v0.1.20
#### Patch
- Expanding fastr team name repl to include draft team on players and qb_meta

---

## v0.1.19
#### Patch
- Adding qb_meta map

---

## v0.1.18
#### Patch
- Added nfelo_games map

---

## v0.1.17
#### Features
- load() now checks that all passed tables have maps upfront to avoid loading data on a request that will fail on a downstream table that was passed incorrectly
- Added list_tables() utility that lists all tables for which there is a map available and can be loaded by the dcm

#### Patch
- Fixed incorrect fields in the team_stadiums map

---

## v0.1.16
#### Patch
- Adding maps for Stadiums datasets

---

## v0.1.15
#### Patch
- Adding handling for nflfastR pipeline bug in the players file that renames draft_round col to draftround

---

## v0.1.14
#### Patch
- Adding retry logic for intermittent failed csv downloads from github

---

## v0.1.13
#### Patch
- Adding fourth down success and conversion to the pbp map for downstream nfelo site build

---

## v0.1.12
#### Patch
- Updated the QB Elo map to include game_id, game_type, and week for linkage to nflfastR sets
- Added QB naming replacement to both rosters and the qbelo to align for merging

---

## v0.1.11
#### Patch
- Adding new fields to the HFA map for downstream nfelo requirements

---

## v0.1.10
#### Patch
- Bad implementation of the score_clean assignment
- Removed season from players.json map

---

## v0.1.9
#### New Maps
- hfa -- Estimated home field advantage
- coaches -- Aggregated coaching stats and headshots
- wt_ratings -- pre-season ratings based on Vegas win totals
- srs_ratings -- in season rankings based on wt_ranking priors and game results

#### Assignments
- score_clean -- added to the games file. Manually cleans the scores of several games that have flipped results

---

## v0.1.8
#### New Maps
- Film Margins -- margins derived from PFF grades
- Market Data -- spread and totals data
- WEPA -- expected points added weighted for predictiveness
- Player Stats, Player Meta -- player files from nflfastR

#### Improvements
- Added testing that ensures all maps and caching are working correctly via test_all_maps()
- Added more checks to ensure a table exists and can be loaded if the map timestamps signal local fresh data exists
- Changed the fastr_team_repl to handle more field structures

---

## v0.1.7
#### Patch
- Updated Actions to use newer versions of checkout and python for node16 to node 20 migration

---

## v0.1.6
#### Features
- Added get_season_state utility that returns the current state of the seasons (ie last week, current week, next week)

#### Patch
- Updated pbp assignments for description based play types

---

## v0.1.5
#### Patch
- Added new assignments and updated the pbp map to prepare for transitioning the wepa model

---

## v0.1.4
#### Patch
- Updated the type of espn_ids in the games map to float as this can be null in the source
- Updated requirement to python 3.11 to ensure proper handling of isoformats

---

## v0.1.3
#### Patch
- Added a check to ensure the local data folder exists

---

## v0.1.2
#### Patch
- Fixed the pyproject toml to distribute a workable package in its entirety

---

## v0.1.1
#### Patch
- Added freshness metadata reset check on package load

---

## v0.1.0
#### Initial Release
- Load and cache pandas dataframes for NFL data
- Initial datasets: pbp, qbelo, games, rosters, qbr, logos, participants
