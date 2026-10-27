# Job Application Tracker

A lightweight, local-first job application tracker. Run a tiny Python server on your machine and manage your applications in the browser — every change is written straight to `applications.csv` on your computer (nothing leaves your machine).

## Features

- Add, edit, and delete applications (company, role, location, date, status, link, description, notes)
- Status dropdown: Wishlist → Applied → Interview → Offer → Rejected
- Sort the applications table by clicking any column header:
  - **Company / Role**, **Location**, **Description**, **Notes** — alphabetical
  - **Applied** — chronological (newest first by default)
  - **Status** — grouped in pipeline order (Wishlist, Applied, Interview, Offer, Rejected)
  - Click the same header again to reverse direction; active sort shows ▲/▼
- Search and filter by status
- Import from CSV, download your data as CSV
- Stats dashboard (`/dashboard`) with KPIs, status bar chart, timeline, and top companies

## Run locally

Requires Python 3.8+ (no dependencies).

```bash
python server.py
# open http://localhost:8000
```

- `http://localhost:8000/` — tracker UI
- `http://localhost:8000/dashboard` — stats dashboard
- `http://localhost:8000/applications.csv` — download your data

## Project structure

```
job-tracker/
├── server.py          # Python HTTP server; backs everything to applications.csv
├── index.html         # Tracker UI (add/edit/delete, sort, search, import/export)
├── dashboard.html     # Stats dashboard (charts + tables)
├── applications.csv   # Your data (created on first run — not committed)
├── .gitignore
└── LICENSE
```

## License

[MIT](LICENSE)
