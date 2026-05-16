# SankalpBackEnd

FastAPI backend + Selenium automation + Google Sheets.

## Structure

```
backend/app/
  api/          auth, dashboard, automation, user, internal
  services/     sheets_service, auth_service, runtime_service, resume_service
  utils/        jwt_utils, security
  models/       schemas.py
  main.py

automation/
  ai/           answer_engine, classifier, cache_manager, ...
  core/         logger, config, storage
  naukri/       login, popup_handler, apply_engine, scheduler
  data/         runtime_state.json, question_history.json, ...
  worker.py
  scheduler.py
  main.py

google-apps-script/Code.gs
```

## Run backend

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Run worker

```bash
cd automation
source venv/bin/activate
pip install -r requirements.txt
export BACKEND_URL=http://localhost:8000 WORKER_API_KEY=worker-dev-key
python worker.py
```

## Run scheduler

```bash
cd automation
python scheduler.py
```
