"""Stockage SQLite + recherche full-text (FTS5).

SQLite suffit largement pour un usage perso : aucun serveur à lancer, un seul
fichier. La recherche utilise FTS5 si disponible, sinon repli sur des LIKE.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone

from . import config
from .models import CanonicalJob

_local = threading.local()
HAS_FTS = True


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    """Connexion propre à chaque thread (FastAPI sert dans un threadpool)."""
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = sqlite3.connect(config.DB_PATH)
        conn.row_factory = sqlite3.Row
        _ensure_schema(conn)
        _local.conn = conn
    return conn


def init() -> None:
    """Crée les tables si besoin (idempotent)."""
    connect()


def _ensure_schema(conn: sqlite3.Connection) -> None:
    global HAS_FTS
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id           INTEGER PRIMARY KEY,
            fingerprint  TEXT UNIQUE,
            source       TEXT NOT NULL,
            source_id    TEXT,
            title        TEXT NOT NULL,
            company      TEXT,
            location     TEXT,
            department   TEXT,
            remote       INTEGER,
            contract_type TEXT,
            description  TEXT,
            url          TEXT,
            salary       TEXT,
            published_at TEXT,
            tags         TEXT,
            first_seen   TEXT,
            last_seen    TEXT
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_dept ON jobs(department)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_published ON jobs(published_at)")

    try:
        conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS jobs_fts USING fts5(
                title, company, description, tags,
                content='jobs', content_rowid='id',
                tokenize='unicode61 remove_diacritics 2'
            )
            """
        )
        # Triggers de synchronisation FTS <-> table jobs.
        conn.executescript(
            """
            CREATE TRIGGER IF NOT EXISTS jobs_ai AFTER INSERT ON jobs BEGIN
                INSERT INTO jobs_fts(rowid, title, company, description, tags)
                VALUES (new.id, new.title, new.company, new.description, new.tags);
            END;
            CREATE TRIGGER IF NOT EXISTS jobs_ad AFTER DELETE ON jobs BEGIN
                INSERT INTO jobs_fts(jobs_fts, rowid, title, company, description, tags)
                VALUES ('delete', old.id, old.title, old.company, old.description, old.tags);
            END;
            CREATE TRIGGER IF NOT EXISTS jobs_au AFTER UPDATE ON jobs BEGIN
                INSERT INTO jobs_fts(jobs_fts, rowid, title, company, description, tags)
                VALUES ('delete', old.id, old.title, old.company, old.description, old.tags);
                INSERT INTO jobs_fts(rowid, title, company, description, tags)
                VALUES (new.id, new.title, new.company, new.description, new.tags);
            END;
            """
        )
        HAS_FTS = True
    except sqlite3.OperationalError:
        # FTS5 indisponible dans ce build SQLite : on retombera sur des LIKE.
        HAS_FTS = False
    conn.commit()


def upsert(job: CanonicalJob) -> bool:
    """Insère l'offre, ou met à jour la version existante (même empreinte).

    Retourne True si c'est une nouvelle offre, False si c'était un doublon.
    En cas de doublon, on conserve la description la plus complète.
    """
    conn = connect()
    now = _now()
    row = conn.execute(
        "SELECT id, description, source FROM jobs WHERE fingerprint = ?",
        (job.fingerprint,),
    ).fetchone()

    if row is None:
        conn.execute(
            """
            INSERT INTO jobs (fingerprint, source, source_id, title, company,
                location, department, remote, contract_type, description, url,
                salary, published_at, tags, first_seen, last_seen)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                job.fingerprint, job.source, job.source_id, job.title, job.company,
                job.location, job.department,
                None if job.remote is None else int(job.remote),
                job.contract_type, job.description, job.url, job.salary,
                job.published_at, json.dumps(job.tags, ensure_ascii=False), now, now,
            ),
        )
        conn.commit()
        return True

    # Doublon : on rafraîchit last_seen, et on garde la description la plus longue.
    existing_desc = row["description"] or ""
    new_desc = job.description or ""
    if len(new_desc) > len(existing_desc):
        conn.execute(
            "UPDATE jobs SET description = ?, salary = COALESCE(?, salary), last_seen = ? WHERE id = ?",
            (new_desc, job.salary, now, row["id"]),
        )
    else:
        conn.execute("UPDATE jobs SET last_seen = ? WHERE id = ?", (now, row["id"]))
    conn.commit()
    return False


def _fts_query(q: str) -> str:
    """Transforme une saisie libre en requête FTS5 sûre (préfixe par token)."""
    import re

    tokens = re.findall(r"[\wÀ-ÿ]+", q)
    if not tokens:
        return '""'
    return " ".join(f'"{t}"*' for t in tokens)


def search(
    q: str | None = None,
    department: str | None = None,
    remote: bool | None = None,
    source: str | None = None,
    limit: int = 100,
    order: str | None = None,
) -> list[dict]:
    """Recherche d'offres. `q` = recherche plein texte ; le reste = filtres exacts.

    `order` : "recent" (date décroissante), "company" (A→Z) ou None (par défaut :
    pertinence si recherche plein texte, sinon date décroissante).
    """
    conn = connect()

    def filters(alias: str = "") -> tuple[list[str], list]:
        parts, params = [], []
        if department:
            parts.append(f"{alias}department = ?")
            params.append(department)
        if remote is not None:
            parts.append(f"{alias}remote = ?")
            params.append(1 if remote else 0)
        if source:
            parts.append(f"{alias}source = ?")
            params.append(source)
        return parts, params

    def order_clause(alias: str = "") -> str:
        if order == "company":
            return f"{alias}company COLLATE NOCASE ASC"
        if order == "recent":
            return f"{alias}published_at DESC"
        return ""

    if q and HAS_FTS:
        where = ["jobs_fts MATCH ?"]
        params: list = [_fts_query(q)]
        fparts, fparams = filters("j.")
        where += fparts
        params += fparams
        sql = (
            "SELECT j.* FROM jobs_fts f JOIN jobs j ON j.id = f.rowid "
            "WHERE " + " AND ".join(where) + " ORDER BY " + (order_clause("j.") or "f.rank") + " LIMIT ?"
        )
        params.append(limit)
    elif q:  # repli sans FTS
        where = ["(title LIKE ? OR company LIKE ? OR description LIKE ?)"]
        like = f"%{q}%"
        params = [like, like, like]
        fparts, fparams = filters("")
        where += fparts
        params += fparams
        sql = "SELECT * FROM jobs WHERE " + " AND ".join(where) + " ORDER BY " + (order_clause() or "published_at DESC") + " LIMIT ?"
        params.append(limit)
    else:
        fparts, fparams = filters("")
        where = fparts if fparts else ["1=1"]
        params = list(fparams)
        sql = "SELECT * FROM jobs WHERE " + " AND ".join(where) + " ORDER BY " + (order_clause() or "published_at DESC") + " LIMIT ?"
        params.append(limit)

    rows = conn.execute(sql, params).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["tags"] = json.loads(d.get("tags") or "[]")
        out.append(d)
    return out


def sources() -> list[str]:
    conn = connect()
    return [r[0] for r in conn.execute("SELECT DISTINCT source FROM jobs ORDER BY source")]


def stats() -> dict:
    conn = connect()
    total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    by_source = {
        r["source"]: r["n"]
        for r in conn.execute("SELECT source, COUNT(*) AS n FROM jobs GROUP BY source ORDER BY n DESC")
    }
    by_dept = {
        r["department"]: r["n"]
        for r in conn.execute(
            "SELECT department, COUNT(*) AS n FROM jobs WHERE department IS NOT NULL GROUP BY department ORDER BY department"
        )
    }
    return {"total": total, "by_source": by_source, "by_department": by_dept}
