from datetime import datetime

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.auth import auth_dependency, authenticate_password, logout
from app.config import get_settings
from app.db import get_connection

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
