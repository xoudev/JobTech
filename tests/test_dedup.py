from jobtech.dedup import fingerprint, normalize_text
from jobtech.models import CanonicalJob


def J(**kw):
    base = dict(source="s", source_id="1", title="t", url="u")
    base.update(kw)
    return CanonicalJob(**base)


def test_normalize_strips_gender_accents_punct():
    assert normalize_text("Développeur (H/F)") == "developpeur"
    assert normalize_text("Data Engineer F/H !") == "data engineer"


def test_same_role_same_fingerprint_across_sources():
    a = J(source="france_travail", title="Développeur Python (H/F)", company="ACME", department="75")
    b = J(source="adzuna", title="developpeur python F/H", company="acme", department="75")
    assert fingerprint(a) == fingerprint(b)


def test_different_department_changes_fingerprint():
    a = J(title="Dev", company="ACME", department="75")
    b = J(title="Dev", company="ACME", department="92")
    assert fingerprint(a) != fingerprint(b)
