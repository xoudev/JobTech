"""Fixtures de test : base SQLite jetable et isolée par test."""
import threading

import pytest

from jobtech import config, db


@pytest.fixture
def fresh_db(tmp_path, monkeypatch):
    """Une base SQLite neuve par test, pointée via config.DB_PATH."""
    db_file = tmp_path / "test.db"
    monkeypatch.setattr(config, "DB_PATH", str(db_file))
    db._local = threading.local()  # oublie toute connexion mise en cache
    db.init()
    yield db
    db._local = threading.local()
