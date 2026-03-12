Create training plans fast

## Compare plan vs results

Use the BikeComputer Pro SQLite backup to compare actual training against a plan.

Example:

```bash
python plan_compare.py --db-path /workspaces/CycleTrainingPlanner/backuped_sessions.db --plan longest_day_2020 --event-date 2020-06-01
```

Compare all plans:

```bash
python plan_compare.py --db-path /workspaces/CycleTrainingPlanner/backuped_sessions.db --all-plans --json-dir /workspaces/CycleTrainingPlanner/sample_json --event-config /workspaces/CycleTrainingPlanner/event_match_config.json
```

Route comparison (planned route GPX vs actual event days):

```bash
python plan_compare.py --db-path /workspaces/CycleTrainingPlanner/backuped_sessions.db --all-plans --json-dir /workspaces/CycleTrainingPlanner/sample_json --event-config /workspaces/CycleTrainingPlanner/event_match_config.json --routes-config /workspaces/CycleTrainingPlanner/routes_map.json --routes-dir /workspaces/CycleTrainingPlanner
```

The routes map can use per-event overrides (see [routes_map.json](routes_map.json)).

Export event summaries:

```bash
python plan_compare.py --db-path /workspaces/CycleTrainingPlanner/backuped_sessions.db --all-plans --json-dir /workspaces/CycleTrainingPlanner/sample_json --event-config /workspaces/CycleTrainingPlanner/event_match_config.json --export-events /workspaces/CycleTrainingPlanner/event_summaries
```

GPX event scan (find rides in the plan's target week):

```bash
python plan_compare.py --db-path /workspaces/CycleTrainingPlanner/backuped_sessions.db --plan nbnw_plan_2023 --gpx-dir /workspaces/CycleTrainingPlanner/sample_gpx
```

VeloHero JSON event scan (merges multiple tracks on the same date):

```bash
python plan_compare.py --db-path /workspaces/CycleTrainingPlanner/backuped_sessions.db --plan nbnw_plan_2023 --json-dir /workspaces/CycleTrainingPlanner/sample_json
```

Event matching config (set a window around the target week or explicit dates):

```bash
python plan_compare.py --db-path /workspaces/CycleTrainingPlanner/backuped_sessions.db --plan nbnw_plan_2023 --json-dir /workspaces/CycleTrainingPlanner/sample_json --event-config /workspaces/CycleTrainingPlanner/event_match_config.json
```

Pick the event source explicitly:

```bash
python plan_compare.py --db-path /workspaces/CycleTrainingPlanner/backuped_sessions.db --plan nbnw_plan_2023 --json-dir /workspaces/CycleTrainingPlanner/sample_json --event-config /workspaces/CycleTrainingPlanner/event_match_config.json --event-source json
```

Config options in [event_match_config.json](event_match_config.json):
- `event_window_days`: include dates within a window around the target week
- `event_dates`: explicit event dates (YYYY-MM-DD)
- `prefer_explicit_event_dates`: use explicit dates if provided
- `event_selection`: `all`, `first_day`, `max_distance`, or `two_day_consecutive_max`
- `event_window_days`: can be combined with `--event-source json|gpx|auto` to pick which data source drives events

Notes:
- `plan_compare.py` uses plan configs embedded in the script.
- Update `DEFAULT_CAT_MULTIPLIERS` in `plan_compare.py` once you know your `sessions.cat` values.
