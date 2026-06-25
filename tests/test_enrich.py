from jobtech.enrich import detect_remote, enrich, extract_tech_tags
from jobtech.models import CanonicalJob


def test_extract_basic_stack():
    tags = extract_tech_tags("Développeur Python / Django, AWS et Docker")
    assert {"Python", "Django", "AWS", "Docker"} <= set(tags)


def test_vue_french_word_not_matched():
    # "vue" est un mot français courant -> ne doit PAS matcher Vue.js
    assert "Vue.js" not in extract_tech_tags("Une vue d'ensemble du poste, reste à définir")
    # mais "Vue.js" oui
    assert "Vue.js" in extract_tech_tags("Stack: Vue.js et Node.js")


def test_no_false_positive_substrings():
    # escalade~scala, reste~rest, trustpilot~rust : aucun ne doit matcher
    assert extract_tech_tags("escalade, le reste de l'équipe, trustpilot") == []


def test_java_is_not_javascript():
    assert "Java" in extract_tech_tags("Backend Java 17")
    assert "Java" not in extract_tech_tags("Frontend JavaScript")
    assert "JavaScript" in extract_tech_tags("Frontend JavaScript")


def test_symbols_cpp_csharp():
    assert "C++" in extract_tech_tags("Dév C++ embarqué")
    assert "C#/.NET" in extract_tech_tags("Développeur .NET / C#")


def test_detect_remote():
    assert detect_remote("Poste en full remote") is True
    assert detect_remote("Télétravail partiel possible") is True
    assert detect_remote("Pas de télétravail") is False
    assert detect_remote("Présentiel uniquement") is False
    assert detect_remote("Développeur backend") is None


def test_enrich_merges_tags_and_sets_remote():
    j = CanonicalJob(
        source="s", source_id="1", title="Data Engineer", url="u",
        description="Spark, Python, Airflow — télétravail hybride", tags=["Existant"],
    )
    enrich(j)
    assert {"Existant", "Python", "Spark", "Airflow"} <= set(j.tags)
    assert j.remote is True


def test_enrich_keeps_existing_remote():
    j = CanonicalJob(source="s", source_id="1", title="x", url="u", remote=False,
                     description="full remote")
    enrich(j)
    assert j.remote is False  # on ne réécrit pas une valeur déjà connue
