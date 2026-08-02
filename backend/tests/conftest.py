import os
import tempfile
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base, get_db
from backend.app.main import app

def pytest_configure(config):
    """Use a fresh caller-owned temp root; Codex and user shells have different ACLs."""
    temp_base = Path(os.environ.get("TEMP", tempfile.gettempdir()))
    root = temp_base / f"sentinelops-pytest-{os.getpid()}-{uuid.uuid4().hex}"
    root.mkdir(parents=True)
    config.option.basetemp=str(root/"pytest")
    config._inicache["cache_dir"] = str(root / "cache")
    tempfile.tempdir=str(root/"runtime")
    Path(tempfile.tempdir).mkdir(exist_ok=True)

@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    yield session
    session.close()

@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
