from datetime import datetime

from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.db import get_connection

app = FastAPI(title="Suibi MVP")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

RECORD_TYPES = ["Log", "Done", "Thought", "Question", "Decision", "Next", "LifeInsight"]


@app.get("/")
def home(request: Request, success: int = 0):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, raw_content, record_type, tags, created_at
            FROM entries
            WHERE date = date('now', 'localtime')
            ORDER BY created_at DESC
            LIMIT 10
            """
        )
        recent_entries = cursor.fetchall()

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "success": bool(success),
            "record_types": RECORD_TYPES,
            "recent_entries": recent_entries,
        },
    )


@app.post("/entries")
def create_entry(
    raw_content: str = Form(...),
    record_type: str = Form(...),
    tags: str = Form(""),
    project: str = Form(""),
):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today = datetime.now().strftime("%Y-%m-%d")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO entries (
                raw_content, record_type, tags, project,
                date, source_type, manual, llm_status, pending,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                raw_content.strip(),
                record_type,
                tags.strip(),
                project.strip() or None,
                today,
                "manual",
                1,
                "pending",
                1,
                now,
                now,
            ),
        )
        conn.commit()

    return RedirectResponse(url="/?success=1", status_code=303)
