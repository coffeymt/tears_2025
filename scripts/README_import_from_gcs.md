Import from GCS - README
=========================

Purpose
-------
This script helps import legacy JSON exports (teams, users, weeks, games, entries, picks)
from a Google Cloud Storage bucket into the application's database. It provides a `--dry-run`
mode to preview actions without persisting changes.

Usage
-----
Run locally where you have Google credentials available (e.g., `GOOGLE_APPLICATION_CREDENTIALS` set):

```powershell
python scripts/import_from_gcs.py --bucket my-bucket --files teams.json,users.json --dry-run
```

Notes
-----
- The script uses the `google-cloud-storage` library and will pick up ADC (Application Default
  Credentials) or credentials pointed to by `GOOGLE_APPLICATION_CREDENTIALS`.
- Currently the script contains scaffolding for `teams` and `users` processing. Later subtasks will
  implement `weeks`, `games`, `entries`, and `picks` with proper idempotent upsert logic.

Dry-run behavior
----------------
When `--dry-run` is provided the script will log the intended upserts and print a summary but will not
perform any writes to the database.
