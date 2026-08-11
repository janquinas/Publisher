import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from backend.main import app
from core.database.config import SessionLocal, init_db
from core.database.models.user import UserDB


@pytest.fixture(autouse=True)
def clean_users():
    # Garantir que as tabelas existam antes de qualquer operacao
    init_db()
    db = SessionLocal()
    try:
        db.query(UserDB).filter(UserDB.email == "nova@teste.com").delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def test_register_creates_session_and_redirects_to_dashboard():
    client = TestClient(app)
    response = client.post(
        "/api/auth/register",
        json={"name": "Nova Pessoa", "email": "nova@teste.com", "password": "senha1234"},
    )

    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["token"]
    assert payload["user"]["name"] == "Nova Pessoa"
    assert payload["user"]["email"] == "nova@teste.com"
