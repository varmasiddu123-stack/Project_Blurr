from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import threading
import json
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parent.parent

# Allow overriding the notes file path via an environment variable. This
# lets hosting providers mount a persistent disk and point `NOTES_PATH`
# at that location (file or directory). If `NOTES_PATH` is a directory,
# we'll use `<NOTES_PATH>/notes.json`.
NOTES_PATH_ENV = os.getenv("NOTES_PATH")
if NOTES_PATH_ENV:
    candidate = Path(NOTES_PATH_ENV)
    if candidate.is_dir():
        NOTES_FILE = candidate / "notes.json"
    else:
        NOTES_FILE = candidate
else:
    DATA_DIR = ROOT / "data"
    NOTES_FILE = DATA_DIR / "notes.json"

class Note(BaseModel):
    id: Optional[str] = None
    title: str
    content: str  # HTML content
    side_notes: Optional[List[str]] = []

class NotesManager:
    def __init__(self, path: Path):
        self.path = path
        self.lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            with self.path.open("w", encoding="utf-8") as f:
                json.dump([], f)

    def _read(self):
        with self.lock:
            with self.path.open("r", encoding="utf-8") as f:
                return json.load(f)

    def _write(self, data):
        with self.lock:
            with self.path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

    def list_notes(self):
        return self._read()

    def get(self, note_id: str):
        notes = self._read()
        for n in notes:
            if n.get("id") == note_id:
                return n
        return None

    def save(self, note: dict):
        notes = self._read()
        if not note.get("id"):
            # create simple id
            import uuid
            note["id"] = str(uuid.uuid4())
            notes.append(note)
        else:
            # update existing
            for i, n in enumerate(notes):
                if n.get("id") == note.get("id"):
                    notes[i] = note
                    break
            else:
                notes.append(note)
        self._write(notes)
        return note


app = FastAPI()

# Serve static frontend
app.mount("/static", StaticFiles(directory=Path(__file__).resolve().parent / "static"), name="static")

notes_mgr = NotesManager(NOTES_FILE)


@app.get("/", response_class=HTMLResponse)
def index():
    idx = Path(__file__).resolve().parent / "static" / "index.html"
    return FileResponse(idx)


@app.get("/api/notes")
def list_notes():
    return notes_mgr.list_notes()


@app.get("/api/notes/{note_id}")
def get_note(note_id: str):
    note = notes_mgr.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@app.post("/api/notes")
def create_or_update(note: Note):
    saved = notes_mgr.save(note.dict())
    return saved
