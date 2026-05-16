# Sankalpa (migrated layout)

The project is split into two folders (same repo root `Git/`):

| Folder | Purpose |
|--------|---------|
| [../sankalpFrontEnd](../sankalpFrontEnd) | React UI |
| [../sankalpBackEnd](../sankalpBackEnd) | FastAPI + automation + Google Sheets |

Legacy paths `frontend/` and `backend/` here are kept for reference; use the new folders for development.

## Quick start

**Backend** — `cd ../sankalpBackEnd/backend && uvicorn app.main:app --reload --port 8000`

**Frontend** — `cd ../sankalpFrontEnd && npm install && npm run dev`

**Worker** — `cd ../sankalpBackEnd/automation && python worker.py`
