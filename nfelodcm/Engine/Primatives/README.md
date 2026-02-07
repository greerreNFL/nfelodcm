# Engine Primatives

This directory contains the core building blocks of the DCM data pipeline. Each primative handles a specific concern in the data loading flow.

## Architecture Overview

```
DCMTable (orchestrator)
    │
    ├── TableMap ──────────────── Loads config from Maps/{table}.json
    │
    ├── Freshness ─────────────── Determines if update needed
    │       │                     - SLA check (seconds since last check)
    │       │                     - GitHub API check (release/commit timestamps)
    │       └── stale_parts ───── For iter tables: list of seasons needing update
    │
    ├── PullManager ───────────── Orchestrates the pull strategy
    │       │
    │       ├── DataPull ──────── Atomic unit: single URL → DataFrame
    │       │
    │       ├── Parts Cache ───── Per-season CSVs in Data/Parts/{table}/
    │       │
    │       └── Assignments ───── Post-pull DataFrame mutations
    │
    └── LocalIO ───────────────── Reads/writes combined CSV in Data/{table}.csv
```

## Components

### TableMap
**File:** `TableMap.py`

Loads and validates table configuration from `Maps/{table}.json`. Read-only at runtime.

- `load_map()` → Returns `TableConfig` or None on failure
- `create_map()` → Developer utility to create new maps

### Freshness
**File:** `Freshness.py`

Determines whether data needs to be updated by checking SLA and remote timestamps.

**Properties:**
- `needs_update: bool` → Whether any update is required
- `stale_parts: Optional[List[int]]` → For iter tables, specific seasons that are stale
- `freshness_check_time: str` → ISO timestamp of when check occurred

**Flow:**
1. `sla_check()` → If within SLA window, skip remote check
2. If SLA breached, call `check_gh_release_freshness()` or `check_gh_commit_freshness()`
3. For `gh_release` iter tables with `IterState`: compare each season's asset timestamp, populate `stale_parts`
4. For `gh_commit` or non-iter: binary `needs_update` flag

### DataPull
**File:** `DataPull.py`

Atomic unit for downloading a single CSV from a URL.

- `pull(url) → DataFrame` → Downloads with retry, returns parsed DataFrame

Uses `with_retry()` for transient error handling. Does not handle iteration, concatenation, or assignments.

### PullManager
**File:** `PullManager.py`

Orchestrates the full pull flow for a table. Replaces the old `DataPull` iteration logic.

**Methods:**
- `update_data(stale_parts=None)` → Main entry point
- `handle_single_pull()` → Non-iter tables: single download
- `handle_iter_pull(stale_parts)` → Iter tables: loop seasons, pull or read cache
- `pull_and_cache_part(season)` → Download season file, write to Parts cache
- `read_cached_part(season)` → Read from Parts cache
- `apply_assignments()` → Run assignment functions on pulled DataFrame

**Caching Strategy:**
- Fresh pulls write to `Data/Parts/{table}/{season}.csv`
- If `stale_parts` is a list, only those seasons are re-downloaded
- If `stale_parts` is None, all seasons are re-downloaded (full pull)
- Cache misses fall back to fresh pull

### LocalIO
**File:** `LocalIO.py`

Handles reading and writing the combined CSV file in `Data/{table}.csv`.

- `read()` → Load CSV into `self.df`
- `write()` → Write `self.df` to CSV
- `loadable()` → Check if file exists and has required columns
- `add_assignment_cols()` → Augment column list with assignment-added columns

### Retry
**File:** `Retry.py`

Shared retry utility with error classification.

**Error Types:**
- `'auth'` → 401/403: No retry, raise `AuthError`
- `'parse'` → 4xx, ValueError, KeyError, TypeError: No retry, raise `ParseError`
- `'retryable'` → 5xx, connection, timeout: Retry with exponential backoff

**Function:**
- `with_retry(fn, max_retries=3, base_delay=1.0, max_delay=30.0, context='')` → Execute fn with retry logic

## Data Flow

### First Load (no cache)
```
DCMTable.__init__()
    → TableMap.load_map()
    → Freshness (SLA fails, checks GitHub API)
        → needs_update = True, stale_parts = None (full pull)
    → PullManager.update_data(stale_parts=None)
        → For each season: DataPull.pull() → write to Parts/
        → Concat all frames
        → apply_assignments()
    → LocalIO.write() → Data/{table}.csv
    → Save TableState, IterState
```

### Incremental Update (cache exists, some seasons stale)
```
DCMTable.__init__()
    → TableMap.load_map()
    → Freshness (SLA breached, checks GitHub API)
        → Compares per-season timestamps
        → needs_update = True, stale_parts = [2024, 2025]
    → PullManager.update_data(stale_parts=[2024, 2025])
        → Seasons 1999-2023: read_cached_part()
        → Seasons 2024-2025: DataPull.pull() → write to Parts/
        → Concat all frames
        → apply_assignments()
    → LocalIO.write() → Data/{table}.csv
    → Save TableState, IterState
```

### Cached Read (within SLA)
```
DCMTable.__init__()
    → TableMap.load_map()
    → Freshness (SLA passes)
        → needs_update = False
    → LocalIO.read() → Load from Data/{table}.csv
```
