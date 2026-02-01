# nfelodcm Test Suite

Unit and integration tests for the nfelodcm package. These tests validate types, configuration, freshness logic, map integrity, assignments, and the public API — all without making network calls.

## Setup

pytest is a dev dependency. Install it with:

```bash
pip install nfelodcm[dev]
```

## Running

From the package root:

```bash
python -m pytest tests/ -v
```

## Test Modules

### `test_types.py` — JsonModel, TableState, SeasonState

Tests the JSON-backed dataclass primitives that underpin state management. Covers default values, save/load round-trips, corrupt file handling, extra key tolerance, and atomic writes.

### `test_table_config.py` — TableConfig Validation

Tests the `TableConfig` dataclass and its `validate()` method, which enforces config structure and map dtype correctness. Covers valid configs, nullable vs non-nullable fields, wrong types, invalid dtypes, nested `IterConfig`/`FreshnessConfig` construction via `from_dict()`, and `to_dict()` round-trips.

### `test_freshness.py` — SLA Logic

Tests the `Freshness` class's SLA check logic without triggering network calls. Covers null timestamps, null SLA seconds, timestamps within and beyond the SLA window, and timestamp comparison logic for determining whether remote data is newer than local.

### `test_maps.py` — Maps/*.json Integrity

Parametrized across all 23 map files. Validates that every map is valid JSON, passes `TableConfig.validate()`, loads into a `TableConfig` instance, contains no mutable state fields (`last_local_update`, `last_freshness_check`), and only references assignments that exist in the registry.

### `test_assignments.py` — Assignment Registry

Tests the assignment registry in `Engine/Assignments/`. Validates that every registered function is callable, that `assignment_columns_added()` returns properly shaped tuples, and that referencing an unregistered assignment raises a `KeyError`.

### `test_public_api.py` — API Contract

Tests the public-facing API surface without triggering downloads. Covers `get_season_state()` return shape, invalid state type handling, `load_maps()` availability, and `TableMap` behavior for nonexistent tables.

## Shared Fixtures (`conftest.py`)

| Fixture | Description |
|---------|-------------|
| `tmp_state_dir` | Temp directory for state file round-trip tests |
| `sample_config_dict` | Valid config as a raw dict (mirrors Maps/*.json shape) |
| `sample_table_config` | `TableConfig` instance built from `sample_config_dict` |
| `sample_table_state` | `TableState` with populated timestamps |

## Note on Smoke Tests

The full integration smoke test (`nfelodcm.test_all_maps()`) lives in `nfelodcm/smoke.py` and is a separate developer tool that downloads all tables and times their loads. It is not part of this pytest suite because it requires network access and is slow.
