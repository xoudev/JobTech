from jobtech.connectors.adzuna import AdzunaConnector
from jobtech.connectors.france_travail import FranceTravailConnector
from jobtech.connectors.jsonld import (
    JsonLdConnector,
    extract_jobpostings,
    iter_jobpostings,
)
from jobtech.connectors.themuse import TheMuseConnector


def test_france_travail_normalize():
    raw = {
        "id": "123ABC",
        "intitule": "Développeur Python (H/F)",
        "entreprise": {"nom": "ACME"},
        "lieuTravail": {"libelle": "75 - PARIS", "codePostal": "75001"},
        "typeContratLibelle": "CDI",
        "salaire": {"libelle": "45k€"},
        "description": "Super poste",
        "origineOffre": {"urlOrigine": "https://ft/123"},
        "dateCreation": "2026-06-01T10:00:00.000Z",
        "competences": [{"libelle": "Python"}, {"libelle": "Git"}],
    }
    j = FranceTravailConnector()._normalize(raw)
    assert j.title == "Développeur Python (H/F)"
    assert j.company == "ACME"
    assert j.department == "75"
    assert j.url == "https://ft/123"
    assert j.contract_type == "CDI"
    assert "Python" in j.tags


def test_adzuna_normalize_extracts_department_and_salary():
    raw = {
        "id": 99,
        "title": "Data Engineer",
        "company": {"display_name": "BetaCorp"},
        "location": {"display_name": "Paris, 75011", "area": ["Île-de-France", "Paris"]},
        "redirect_url": "https://adzuna/99",
        "description": "desc",
        "created": "2026-06-02T00:00:00Z",
        "salary_min": 40000,
        "salary_max": 50000,
        "category": {"label": "IT Jobs"},
        "contract_time": "permanent",
    }
    j = AdzunaConnector()._normalize(raw)
    assert j.title == "Data Engineer"
    assert j.company == "BetaCorp"
    assert j.department == "75"  # déduit de "75011"
    assert j.url == "https://adzuna/99"
    assert j.salary and "€" in j.salary


def test_themuse_normalize_strips_html_and_detects_paris():
    raw = {
        "id": 5,
        "name": "Backend Engineer",
        "company": {"name": "Muse Inc"},
        "locations": [{"name": "Paris, France"}],
        "refs": {"landing_page": "https://muse/5"},
        "contents": "<p>We use <b>Python</b></p>",
        "publication_date": "2026-06-03T00:00:00Z",
        "type": "Full Time",
        "levels": [{"name": "Senior"}],
        "categories": [{"name": "Software Engineering"}],
    }
    j = TheMuseConnector()._normalize(raw)
    assert j.title == "Backend Engineer"
    assert j.department == "75"
    assert "<" not in (j.description or "")
    assert "Senior" in j.tags


def test_jsonld_extraction_and_normalize():
    html = """
    <html><head>
    <script type="application/ld+json">
    {"@context":"https://schema.org","@type":"JobPosting",
     "title":"DevOps Engineer","datePosted":"2026-06-04",
     "hiringOrganization":{"@type":"Organization","name":"Cloud SAS"},
     "jobLocation":{"@type":"Place","address":{"@type":"PostalAddress",
        "addressLocality":"Paris","postalCode":"75009"}},
     "employmentType":"FULL_TIME","jobLocationType":"TELECOMMUTE",
     "url":"https://site/job/1","description":"<p>Kubernetes &amp; Terraform</p>"}
    </script></head><body></body></html>
    """
    postings = extract_jobpostings(html)
    assert len(postings) == 1
    j = JsonLdConnector().normalize(postings[0], source_url="https://site")
    assert j.title == "DevOps Engineer"
    assert j.company == "Cloud SAS"
    assert j.department == "75"
    assert j.remote is True
    assert j.url == "https://site/job/1"


def test_jsonld_handles_graph_and_itemlist():
    doc = {
        "@context": "x",
        "@graph": [
            {"@type": "WebPage"},
            {"@type": ["JobPosting"], "title": "A", "url": "u1"},
            {"@type": "ItemList", "itemListElement": [
                {"@type": "JobPosting", "title": "B", "url": "u2"},
            ]},
        ],
    }
    titles = sorted(p.get("title") for p in iter_jobpostings(doc))
    assert titles == ["A", "B"]
