"""Petite UI de recherche (FastAPI + Jinja2)."""
from __future__ import annotations

import hashlib
import os
import threading
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .. import config, db, pipeline

# Étiquettes lisibles des sources (pour les badges).
SOURCE_LABELS = {
    "france_travail": "France Travail",
    "adzuna": "Adzuna",
    "themuse": "The Muse",
    "jsonld": "Carrières",
}

# Technos mises en avant sous la barre de recherche.
POPULAR_TECHS = ["Python", "React", "AWS", "TypeScript", "Java", "Kubernetes", "Go", "Docker"]

_collecting = {"running": False}


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init()
    yield


app = FastAPI(title="JobTech", description="Offres IT en Île-de-France", lifespan=lifespan)
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))


def _date_label(iso: str | None) -> str:
    """Date ISO -> libellé relatif (« aujourd'hui », « hier », « il y a 5 j »…)."""
    if not iso:
        return ""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return iso[:10]
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    days = (datetime.now(timezone.utc) - dt).days
    if days <= 0:
        return "aujourd'hui"
    if days == 1:
        return "hier"
    if days < 30:
        return f"il y a {days} j"
    return dt.strftime("%d/%m/%Y")


def _avatar(company: str | None) -> tuple[str, int]:
    """Initiale + teinte déterministe pour l'avatar de l'entreprise."""
    name = (company or "?").strip()
    initial = next((c for c in name if c.isalnum()), "?").upper()
    hue = int(hashlib.sha1(name.encode("utf-8")).hexdigest(), 16) % 360
    return initial, hue


def _decorate(jobs: list[dict]) -> list[dict]:
    for j in jobs:
        j["date_label"] = _date_label(j.get("published_at"))
        j["source_label"] = SOURCE_LABELS.get(j.get("source"), j.get("source"))
        j["avatar_initial"], j["avatar_hue"] = _avatar(j.get("company"))
    return jobs


@app.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    q: str = "",
    dept: str = "",
    remote: str = "",
    source: str = "",
    order: str = "recent",
    collect: str = "",
) -> HTMLResponse:
    remote_val = True if remote == "on" else None
    jobs = db.search(
        q=q or None,
        department=dept or None,
        remote=remote_val,
        source=source or None,
        order=order or None,
        limit=200,
    )
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "jobs": _decorate(jobs),
            "q": q,
            "dept": dept,
            "remote": remote,
            "source": source,
            "order": order,
            "departments": config.IDF_DEPT_NAMES,
            "sources": db.sources(),
            "source_labels": SOURCE_LABELS,
            "popular": POPULAR_TECHS,
            "stats": db.stats(),
            "collect_started": collect == "started",
            "collecting": _collecting["running"],
        },
    )


@app.post("/collect")
def collect() -> RedirectResponse:
    """Lance une collecte en arrière-plan (ne bloque pas la requête)."""
    def run() -> None:
        try:
            pipeline.run_collection()
        finally:
            _collecting["running"] = False

    if not _collecting["running"]:
        _collecting["running"] = True
        threading.Thread(target=run, daemon=True).start()
    return RedirectResponse("/?collect=started", status_code=303)


@app.get("/api/jobs")
def api_jobs(q: str = "", dept: str = "", remote: str = "", source: str = "", limit: int = 200) -> JSONResponse:
    remote_val = True if remote == "on" else None
    jobs = db.search(q=q or None, department=dept or None, remote=remote_val, source=source or None, limit=limit)
    return JSONResponse({"count": len(jobs), "jobs": jobs})


@app.get("/api/stats")
def api_stats() -> JSONResponse:
    return JSONResponse(db.stats())
