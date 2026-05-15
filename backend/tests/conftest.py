import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.main import app as _app


@pytest.fixture
def app() -> FastAPI:
    return _app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)
