import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_swachchhohat.db"
os.environ["SECRET_KEY"] = "test-key-not-for-production-1234567890"

import pytest
from fastapi.testclient import TestClient

from app.core.db import Base, engine
from app.main import app


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    test_db = Path("test_swachchhohat.db")
    if test_db.exists():
        test_db.unlink()

