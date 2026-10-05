import pytest
from pathlib import Path
from api.models import Teacher, Student, TaskJob
from api.security import hash_password, get_current_user

TEST_PDF_PATH = Path(__file__).resolve().parent.parent / "test_course_material.pdf"


@pytest.fixture
def test_teacher(db_session):
    teacher = db_session.query(Teacher).filter(Teacher.email == "swagger_teacher@test.com").first()
    if not teacher:
        teacher = Teacher(
            name="Swagger Teacher",
            email="swagger_teacher@test.com",
            password_hash=hash_password("TeacherSecret!"),
            subject="Mathematics",
        )
        db_session.add(teacher)
        db_session.commit()
        db_session.refresh(teacher)
    return teacher


@pytest.fixture
def test_student(db_session):
    student = db_session.query(Student).filter(Student.email == "swagger_student@test.com").first()
    if not student:
        student = Student(
            name="Swagger Student",
            email="swagger_student@test.com",
            roll_number="STU-9999",
            password_hash=hash_password("StudentSecret!"),
        )
        db_session.add(student)
        db_session.commit()
        db_session.refresh(student)
    return student


def test_existing_json_login_endpoint(client, test_teacher):
    """Requirement 2: Existing JSON login endpoint POST /auth/login must continue working exactly as before."""
    response = client.post(
        "/auth/login",
        json={
            "email": "swagger_teacher@test.com",
            "password": "TeacherSecret!",
            "role": "teacher",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "teacher"
    assert data["user_id"] == test_teacher.id


def test_swagger_token_endpoint_teacher(client, test_teacher):
    """Requirements 3 & 4: POST /auth/token authenticates teacher with form data and returns access_token."""
    response = client.post(
        "/auth/token",
        data={
            "username": "swagger_teacher@test.com",
            "password": "TeacherSecret!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Verify protected profile endpoint accepts this token
    token = data["access_token"]
    profile_res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert profile_res.status_code == 200
    profile_data = profile_res.json()
    assert profile_data["email"] == "swagger_teacher@test.com"
    assert profile_data["role"] == "teacher"


def test_swagger_token_endpoint_student(client, test_student):
    """Requirement 4: POST /auth/token authenticates student with form data."""
    response = client.post(
        "/auth/token",
        data={
            "username": "swagger_student@test.com",
            "password": "StudentSecret!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    token = data["access_token"]
    profile_res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert profile_res.status_code == 200
    profile_data = profile_res.json()
    assert profile_data["email"] == "swagger_student@test.com"
    assert profile_data["role"] == "student"


def test_swagger_token_invalid_credentials(client, test_teacher):
    """POST /auth/token rejects invalid password with 401."""
    response = client.post(
        "/auth/token",
        data={
            "username": "swagger_teacher@test.com",
            "password": "WrongPassword!",
        },
    )
    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers


def test_openapi_security_scheme(client):
    """Requirement 8: Swagger's OpenAPI security configuration points to /auth/token."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    openapi = response.json()
    schemes = openapi.get("components", {}).get("securitySchemes", {})
    assert "OAuth2PasswordBearer" in schemes
    flow = schemes["OAuth2PasswordBearer"].get("flows", {}).get("password", {})
    assert flow.get("tokenUrl") == "/auth/token"


def test_exams_endpoints_require_authentication(client):
    """Requirements 9 & 10: GET /exams/ and POST /exams/generate-ai reject unauthorized requests."""
    res_list = client.get("/exams/")
    assert res_list.status_code == 401

    res_get = client.get("/exams/1")
    assert res_get.status_code == 401

    with open(TEST_PDF_PATH, "rb") as f:
        pdf_bytes = f.read()

    res_gen = client.post(
        "/exams/generate-ai",
        files={"pdf_file": ("test.pdf", pdf_bytes, "application/pdf")},
        data={"title": "Test AI Exam"},
    )
    assert res_gen.status_code == 401


def test_generate_ai_exam_celery_flow(client, test_teacher):
    """Requirement: Swagger -> /auth/token -> JWT -> POST /exams/generate-ai -> 202 with task_id."""
    # 1. Obtain token via /auth/token
    login_res = client.post(
        "/auth/token",
        data={
            "username": "swagger_teacher@test.com",
            "password": "TeacherSecret!",
        },
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Call POST /exams/generate-ai with Authorization Bearer
    from unittest.mock import patch

    mock_questions = [
        {
            "question_type": "mcq",
            "question_text": "What is a queue?",
            "options": ["A. FIFO", "B. LIFO"],
            "correct_answer": "A. FIFO",
            "marks": 2.0,
            "topic": "Data Structures",
            "difficulty": "medium",
            "question_number": 1,
        }
    ]

    with open(TEST_PDF_PATH, "rb") as f:
        pdf_bytes = f.read()

    with patch("tasks.exam_tasks.generate_exam_from_text", return_value=mock_questions):
        gen_res = client.post(
            "/exams/generate-ai",
            headers=headers,
            files={"pdf_file": ("test_course_material.pdf", pdf_bytes, "application/pdf")},
            data={
                "title": "Automated AI Exam",
                "total_marks": "30.0",
                "num_mcq": "2",
                "num_fill_blanks": "1",
                "num_subjective": "1",
                "strictness": "medium",
            },
        )

    # 3. Verify HTTP 202 Accepted and task_id returned
    assert gen_res.status_code == 202
    res_data = gen_res.json()
    assert "task_id" in res_data
    assert res_data["task_id"] > 0
    assert res_data["status"] in ("QUEUED", "COMPLETED")
    assert "task" in res_data["message"].lower() or "queued" in res_data["message"].lower()


def test_generate_ai_exam_forbidden_for_student(client, test_student):
    """Students cannot call POST /exams/generate-ai."""
    login_res = client.post(
        "/auth/token",
        data={
            "username": "swagger_student@test.com",
            "password": "StudentSecret!",
        },
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    with open(TEST_PDF_PATH, "rb") as f:
        pdf_bytes = f.read()

    gen_res = client.post(
        "/exams/generate-ai",
        headers=headers,
        files={"pdf_file": ("test.pdf", pdf_bytes, "application/pdf")},
        data={"title": "Unauthorized Student Exam"},
    )
    assert gen_res.status_code == 403
