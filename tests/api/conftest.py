"""Shared FastAPI test client."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client():
    """Return FastAPI test client."""

    return TestClient(app)
