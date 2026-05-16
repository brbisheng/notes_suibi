from pathlib import Path
from datetime import datetime

from fastapi import Depends, FastAPI, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.auth import auth_dependency, authenticate_password, logout
from app.config import get_settings
from app.db import get_connection
from app.importers.codex_jsonl import import_codex_jsonl

app = FastAPI(title="Suibi MVP")
app.add_middleware(
    SessionMiddleware,
    secret_key=get_settings().session_secret,
    session_cookie="suibi_session",
    same_site="lax",
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

RECORD_TYPES = ["Log", "Done", "Thought", "Question", "Decision", "Next", "LifeInsight"]


@app.get("/login")
def login_page(request: Request):
    if request.session.get("is_authenticated"):
        return RedirectResponse(url="/", status_code=303)

    return templates.TemplateResponse(
        request,
        "login.html",
        {
            "error": request.query_params.get("error"),
            "remaining_attempts": request.query_params.get("remaining_attempts"),
            "locked_until": request.query_params.get("locked_until"),
        },
    )


@app.post("/login")
def login(request: Request, password: str = Form(...)):
    state = authenticate_password(request, password)
    if state.ok:
        return RedirectResponse(url="/", status_code=303)

    params = f"error={state.error}&remaining_attempts={state.remaining_attempts}"
    if state.locked_until:
        params += f"&locked_until={state.locked_until}"
    return RedirectResponse(url=f"/login?{params}", status_code=303)


@app.post("/logout")
def do_logout(request: Request):
    logout(request)
    return RedirectResponse(url="/login", status_code=303)


@app.get("/")
def home(request: Request, success: int = 0, _: None = Depends(auth_dependency)):
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
    _: None = Depends(auth_dependency),
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


@app.get("/import")
def import_page(request: Request, _: None = Depends(auth_dependency)):
    return templates.TemplateResponse(request, "import.html", {})


@app.post("/import")
def import_codex_file(file: UploadFile = File(...), _: None = Depends(auth_dependency)):
    tmp_dir = Path("data/imports/tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp_path = tmp_dir / (file.filename or "upload.jsonl")
    with tmp_path.open("wb") as out:
        out.write(file.file.read())

    import_id = import_codex_jsonl(tmp_path)
    return RedirectResponse(url=f"/import/{import_id}", status_code=303)


@app.get("/import/{import_id}")
def import_detail(import_id: int, request: Request, _: None = Depends(auth_dependency)):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM raw_imports WHERE id = ?", (import_id,))
        raw = cursor.fetchone()
        cursor.execute(
            """
            SELECT st.user_request, st.final_summary, s.source_session_id, s.project_path
            FROM session_turns st
            JOIN sessions s ON s.id = st.session_id
            WHERE s.raw_import_id = ?
            ORDER BY st.id ASC
            LIMIT 50
            """,
            (import_id,),
        )
        turns = cursor.fetchall()

    if raw is None:
        return RedirectResponse(url="/import", status_code=303)

    return templates.TemplateResponse(
        request,
        "import_detail.html",
        {"raw": raw, "turns": turns},
    )
