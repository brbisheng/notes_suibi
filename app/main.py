from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.config import get_settings

app = FastAPI(title="Suibi MVP")


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    settings = get_settings()
    return (
        "<h1>Suibi MVP</h1>"
        "<p>Service is running.</p>"
        f"<p>DB Path: {settings.db_path}</p>"
    )
