from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
import os
import uuid

from sqlalchemy import create_engine, Column, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON as SQLAlchemyJSON

ROOT = Path(__file__).resolve().parent.parent

# Configuration: support DATABASE_URL for Postgres, otherwise fall back to
# file-based JSON storage (NOTES_PATH handled earlier in README).
DATABASE_URL = os.getenv("DATABASE_URL")

Base = declarative_base()
engine = None
SessionLocal = None


class NoteORM(Base):
    __tablename__ = "notes"
    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    # Use JSONB for Postgres, SQLAlchemy JSON for other engines
    content_json = Column(SQLAlchemyJSON)


class Note(BaseModel):
    id: Optional[str] = None
    title: str
    content: str  # HTML content
    side_notes: Optional[List[str]] = []


def init_db():
    global engine, SessionLocal
    if DATABASE_URL:
        engine = create_engine(DATABASE_URL, future=True)
        SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
        Base.metadata.create_all(bind=engine)


def db_list_notes():
    session = SessionLocal()
    try:
        rows = session.query(NoteORM).all()
        result = []
        for r in rows:
            side = r.content_json.get("side_notes") if r.content_json else []
            result.append({"id": r.id, "title": r.title, "content": r.content, "side_notes": side})
        return result
    finally:
        session.close()


def db_get_note(note_id: str):
    session = SessionLocal()
    try:
        r = session.get(NoteORM, note_id)
        if not r:
            return None
        side = r.content_json.get("side_notes") if r.content_json else []
        return {"id": r.id, "title": r.title, "content": r.content, "side_notes": side}
    finally:
        session.close()


def db_save(note: dict):
    session = SessionLocal()
    try:
        nid = note.get("id") or str(uuid.uuid4())
        r = session.get(NoteORM, nid)
        if r:
            r.title = note.get("title")
            r.content = note.get("content")
            r.content_json = {"side_notes": note.get("side_notes", [])}
        else:
            r = NoteORM(id=nid, title=note.get("title"), content=note.get("content"), content_json={"side_notes": note.get("side_notes", [])})
            session.add(r)
        session.commit()
        return {"id": r.id, "title": r.title, "content": r.content, "side_notes": r.content_json.get("side_notes", [])}
    finally:
        session.close()


app = FastAPI()

# Serve static frontend
app.mount("/static", StaticFiles(directory=Path(__file__).resolve().parent / "static"), name="static")

# Initialize DB if configured
init_db()

# If DATABASE_URL is set, use DB-backed functions; otherwise fall back to file storage
USE_DB = DATABASE_URL is not None

if not USE_DB:
    # fallback file-based storage, keep previous simple implementation
    import threading, json

    # Determine notes file path
    NOTES_PATH_ENV = os.getenv("NOTES_PATH")
    if NOTES_PATH_ENV:
        NOTES_FILE = Path(NOTES_PATH_ENV)
        if NOTES_FILE.is_dir():
            NOTES_FILE = NOTES_FILE / "notes.json"
    else:
        DATA_DIR = ROOT / "data"
        NOTES_FILE = DATA_DIR / "notes.json"

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
                nid = str(uuid.uuid4())
                note["id"] = nid
                notes.append(note)
            else:
                for i, n in enumerate(notes):
                    if n.get("id") == note.get("id"):
                        notes[i] = note
                        break
                else:
                    notes.append(note)
            self._write(notes)
            return note

    notes_mgr = NotesManager(NOTES_FILE)


@app.get("/", response_class=HTMLResponse)
def index():
    idx = Path(__file__).resolve().parent / "static" / "index.html"
    return FileResponse(idx)


@app.get("/api/notes")
def list_notes():
    if USE_DB:
        return db_list_notes()
    return notes_mgr.list_notes()


@app.get("/api/notes/{note_id}")
def get_note(note_id: str):
    if USE_DB:
        note = db_get_note(note_id)
    else:
        note = notes_mgr.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@app.post("/api/notes")
def create_or_update(note: Note):
    payload = note.dict()
    if USE_DB:
        saved = db_save(payload)
    else:
        saved = notes_mgr.save(payload)
    return saved
