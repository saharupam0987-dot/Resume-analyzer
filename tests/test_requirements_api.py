import json
import pytest
from pathlib import Path
from api.models import Student, Teacher
from api.security import hash_password, create_access_token

TEST_PDF_PATH = Path(__file__).resolve().parent.parent / "test_course_material.pdf"


@pytest.fixture
def student_auth_headers(db_session):
    student = db_session.query(Student).filter(Student.email == "student_test_phase1@test.com").first()
    if not student:
        student = Student(
            name="Phase1 Student",
            email="student_test_phase1@test.com",
            roll_number="STU-PHASE1",
            password_hash=hash_password("StudentPass123!"),
        )
        db_session.add(student)
        db_session.commit()
        db_session.refresh(student)

    token = create_access_token({"sub": str(student.id), "role": "student", "email": student.email})
    return {"Authorization": f"Bearer {token}"}


def test_parse_requirements_teacher_authorized(client, teacher_auth_headers):
    """Teachers can parse exam requirements into structured blueprint."""
    payload = {
        "subject": "Theory of Computation",
        "total_marks": 100,
        "duration_minutes": 180,
        "requirements": (
            "Create a difficult university-style Theory of Computation paper. "
            "Give 2 DFA questions, one should be a construction problem. "
            "Give one difficult NFA to DFA conversion question. "
            "Include a 10-mark CFG ambiguity problem. "
            "Avoid direct definition questions."
        )
    }
    response = client.post("/exams/requirements/parse", json=payload, headers=teacher_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "blueprint" in data
    blueprint = data["blueprint"]
    assert blueprint["subject"] == "Theory of Computation"
    assert blueprint["global_requirements"]["university_style"] is True
    assert blueprint["global_requirements"]["avoid_direct_definitions"] is True
    assert len(blueprint["question_requirements"]) >= 3


def test_parse_requirements_student_forbidden(client, student_auth_headers):
    """Students cannot access exam requirements parser."""
    payload = {
        "subject": "Theory of Computation",
        "requirements": "Give 2 DFA questions."
    }
    response = client.post("/exams/requirements/parse", json=payload, headers=student_auth_headers)
    assert response.status_code == 403


def test_parse_requirements_unauthenticated(client):
    """Unauthenticated users cannot parse requirements."""
    response = client.post("/exams/requirements/parse", json={"requirements": "Give 2 DFA questions."})
    assert response.status_code == 401


def test_parse_requirements_empty_string(client, teacher_auth_headers):
    """Empty requirements string returns 400 Bad Request."""
    response = client.post(
        "/exams/requirements/parse",
        json={"requirements": "   "},
        headers=teacher_auth_headers,
    )
    assert response.status_code == 400


def test_generate_ai_with_blueprint(client, teacher_auth_headers, tmp_path):
    """Verifies that POST /exams/generate-ai accepts an optional blueprint and triggers Celery generation."""
    # Create mock PDF if needed
    pdf_path = TEST_PDF_PATH
    if not pdf_path.exists():
        pdf_path = tmp_path / "test_doc.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 Mock PDF text content for test")

    blueprint = {
        "subject": "Theory of Computation",
        "total_marks": 50,
        "global_requirements": {
            "difficulty": "hard",
            "university_style": True,
            "avoid_direct_definitions": True,
        },
        "question_requirements": [
            {
                "topic": "DFA",
                "count": 2,
                "question_type": "construction",
                "difficulty": "medium",
            }
        ]
    }

    from unittest.mock import patch

    mock_questions = [
        {
            "question_type": "construction",
            "question_text": "Construct a DFA that accepts strings ending with '01'.",
            "options": [],
            "correct_answer": "DFA state transition table and diagram specification.",
            "marks": 10.0,
            "topic": "DFA",
            "difficulty": "hard",
            "question_number": 1,
        }
    ]

    with open(pdf_path, "rb") as f:
        with patch("tasks.exam_tasks.generate_exam_from_text", return_value=mock_questions):
            response = client.post(
                "/exams/generate-ai",
                data={
                    "title": "Phase 1 Blueprint Exam",
                    "total_marks": 50.0,
                    "num_mcq": 2,
                    "num_fill_blanks": 0,
                    "num_subjective": 1,
                    "strictness": "hard",
                    "blueprint": json.dumps(blueprint),
                },
                files={"pdf_file": ("test_course_material.pdf", f, "application/pdf")},
                headers=teacher_auth_headers,
            )

    assert response.status_code == 202
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "QUEUED"
