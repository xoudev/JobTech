from fastapi.testclient import TestClient

from jobtech.dedup import fingerprint
from jobtech.models import CanonicalJob


def _seed(db):
    j = CanonicalJob(
        source="themuse", source_id="1", title="Data Engineer", company="BetaCorp",
        department="92", url="https://x/1", description="Spark, Python",
    )
    j.fingerprint = fingerprint(j)
    db.upsert(j)


def test_index_and_api(fresh_db):
    _seed(fresh_db)
    from jobtech.web.app import app

    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    assert "Data Engineer" in r.text

    assert client.get("/api/jobs?q=python").json()["count"] == 1
    assert client.get("/api/jobs?dept=92").json()["count"] == 1
    assert client.get("/api/jobs?dept=75").json()["count"] == 0
    assert client.get("/api/stats").json()["total"] == 1
