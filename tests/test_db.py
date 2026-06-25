from jobtech.dedup import fingerprint
from jobtech.models import CanonicalJob


def J(**kw):
    base = dict(source="s", source_id="1", title="t", url="u")
    base.update(kw)
    j = CanonicalJob(**base)
    j.fingerprint = fingerprint(j)
    return j


def test_upsert_new_then_dedup_keeps_longest_description(fresh_db):
    db = fresh_db
    a = J(source="france_travail", title="Dev Python (H/F)", company="ACME",
          department="75", description="court")
    b = J(source="adzuna", title="dev python F/H", company="acme",
          department="75", description="x" * 200)
    assert db.upsert(a) is True
    assert db.upsert(b) is False  # même empreinte -> doublon
    assert db.stats()["total"] == 1
    assert len(db.search()[0]["description"]) == 200  # la plus complète est gardée


def test_search_fulltext_and_filters(fresh_db):
    db = fresh_db
    db.upsert(J(title="Développeur Python", company="A", department="75", description="django"))
    db.upsert(J(source="x", source_id="2", title="Data Engineer", company="B",
                department="92", description="spark airflow"))
    assert len(db.search(q="python")) == 1
    assert len(db.search(q="developpeur")) == 1            # diacritiques ignorés
    assert len(db.search(department="92")) == 1
    assert [r["title"] for r in db.search(q="airflow")] == ["Data Engineer"]
    assert db.stats()["total"] == 2
    assert set(db.sources()) == {"s", "x"}
