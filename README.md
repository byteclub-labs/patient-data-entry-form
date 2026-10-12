# patient-data-entry-form
Basic patient data entry form (built by the Devin software factory)

A single-page intake form for registering a new patient, backed by a small
Python standard-library server and a SQLite store. Demo app — not for real
patient data.

## Run locally

```sh
python3 server.py
```

Then open http://localhost:8000. Set `PORT` to use a different port:

```sh
PORT=8080 python3 server.py
```

No dependencies, accounts, or build step — Python 3 only.

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/patients` | All entered patients, newest first |
| `POST` | `/api/patients` | Create a patient (`201` + the record; `400 {"error": ...}` on invalid input) |

## Data

Records are stored in `data/patients.db` (SQLite), created automatically on
first run and gitignored.

