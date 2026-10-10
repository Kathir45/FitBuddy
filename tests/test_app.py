import os

os.environ["DATABASE_URL"] = "sqlite:///./test_fitbuddy.db"
os.environ["ADMIN_KEY"] = "test-admin"

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_home_page():

    response = client.get("/")

    assert response.status_code == 200

    assert "FitBuddy" in response.text


def test_health():

    response = client.get(
        "/api/health"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"


def test_invalid_feedback():

    response = client.post(
        "/submit-feedback",
        data={
            "user_id": "A",
            "feedback": "x",
        },
    )

    assert response.status_code in [
        404,
        422,
    ]