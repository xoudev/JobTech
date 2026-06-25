"""Petite UI de recherche (FastAPI + Jinja2)."""
from __future__ import annotations

import os

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from .. import config, db

app = FastAPI(title="JobTech", description="Offres IT en Île-de-France")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))


@app.on_event("startup")
def _startup() -> None:
    db.init()


@app.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    q: str = "",
    dept: str = "",
    remote: str = "",
    source: str = "",
) -> HTMLResponse:
    remote_val = True if remote == "on" else None
    jobs = db.search(
        q=q or None,
        department=dept or None,
        remote=remote_val,
        source=source or None,
        limit=200,
    )
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "jobs": jobs,
            "q": q,
            "dept": dept,
            "remote": remote,
            "source": source,
            "departments": config.IDF_DEPT_NAMES,
            "sources": db.sources(),
            "stats": db.stats(),
        },
    )


@app.get("/api/jobs")
def api_jobs(q: str = "", dept: str = "", remote: str = "", source: str = "", limit: int = 200) -> JSONResponse:
    remote_val = True if remote == "on" else None
    jobs = db.search(q=q or None, department=dept or None, remote=remote_val, source=source or None, limit=limit)
    return JSONResponse({"count": len(jobs), "jobs": jobs})


@app.get("/api/stats")
def api_stats() -> JSONResponse:
    return JSONResponse(db.stats())
