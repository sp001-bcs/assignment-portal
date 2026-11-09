import pytest
import storage
from app import create_app

VALID = {
    "name": "Ali Khan",
    "reg_no": "FA22-BSE-001",
    "title": "Lab 5 - Git Basics",
    "url": "https://github.com/alikhan/lab5",
}


@pytest.fixture
def client_and_file(tmp_path):
    data_file = str(tmp_path / "submissions.json")
    app = create_app(data_file)
    app.config["TESTING"] = True
    return app.test_client(), data_file


def test_valid_submission_is_saved_and_listed(client_and_file):
    client, data_file = client_and_file
    response = client.post("/submit", data=VALID)
    assert response.status_code == 200
    saved = storage.load(data_file)
    assert len(saved) == 1 and saved[0]["reg_no"] == "FA22-BSE-001"
    page = client.get("/").get_data(as_text=True)
    assert "Lab 5 - Git Basics" in page


def test_missing_registration_number_is_rejected(client_and_file):
    client, data_file = client_and_file
    response = client.post("/submit", data={**VALID, "reg_no": ""})
    assert response.status_code == 400
    assert "Registration number is required." in response.get_data(as_text=True)
    assert storage.load(data_file) == []


def test_invalid_url_is_rejected_and_not_saved(client_and_file):
    client, data_file = client_and_file
    response = client.post("/submit", data={**VALID, "url": "not-a-valid-link"})
    assert response.status_code == 400
    assert "Submission URL must be a valid http(s) link." in response.get_data(as_text=True)
    assert storage.load(data_file) == []
