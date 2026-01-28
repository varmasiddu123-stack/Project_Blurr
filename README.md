# Minimal Notion-like Notes App

This project is a minimal notes app with a simple editor (headlines, highlights, circle, side-notes) and a small FastAPI backend storing notes in JSON.

Setup (Windows)
1. Install Python 3.10+
2. Create virtualenv and activate:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

3. Install requirements:

```powershell
pip install -r requirements.txt
```

4. Run server:

```powershell
uvicorn app.main:app --reload --port 8000
```

5. Open http://localhost:8000

Run tests:

```powershell
pytest -q
```

Deploying to Render (free tier) or other hosts
------------------------------------------------

1. Create a GitHub repository and push this project:

```bash
git init
git add .
git commit -m "initial"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

2. On Render (https://render.com), click "New +" → "Web Service" → "Connect a repository" and pick your repo. Use the default build command and set the start command to:

```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Render will detect the Dockerfile if you enable Docker, or run using the `Procfile` above. The app will be reachable at the Render-assigned domain.

Alternate quick deploys:
- Replit: import from GitHub and run the `uvicorn` command.
- Docker: build locally with `docker build -t notes-app .` and run `docker run -p 8000:8000 -e PORT=8000 notes-app`.

Persistent storage on Render
----------------------------

By default the app stores notes in `data/notes.json` inside the container. On Render this filesystem is ephemeral and may be lost after redeploys or instance restarts. To make notes persistent you can attach a Render Persistent Disk and point the app to store notes there.

Steps:

1. In the Render dashboard open your service and click **Disks** → **Add Disk**. Create a disk and choose a mount point (for example `/data`).
2. In your service settings add an environment variable `NOTES_PATH` with the value `/data/notes.json` (or a directory like `/data` — the app will use `/data/notes.json`).
3. Redeploy the service (or push a new commit). The app will write notes to the path specified by `NOTES_PATH` and those files will persist across restarts.

Quick test after deploy:

```powershell
curl -i https://<your-service>.onrender.com/api/notes
```

If you prefer a managed database instead (Postgres), I can help migrate the storage to Postgres and update the app accordingly.

Files of interest:
- `app/main.py` — backend + simple file-based storage
- `app/static` — frontend files
- `data/notes.json` — sample dataset

If you'd like, I can run the test suite here or help you deploy this to a free host.
