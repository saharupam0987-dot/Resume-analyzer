import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.models import Teacher, Student, Exam, Question, ClassRoom, Enrollment, ExamAssignment, Submission
from api.security import hash_password, create_access_token


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_setup(db_session):
    # Teacher A
    teacher_a = Teacher(name="Teacher A", email="teacher_a@test.com", password_hash=hash_password("password123"))
    # Teacher B
    teacher_b = Teacher(name="Teacher B", email="teacher_b@test.com", password_hash=hash_password("password123"))
    # Student 1
    student_1 = Student(name="Student One", email="student1@test.com", roll_number="S001", password_hash=hash_password("password123"))
    # Student 2
    student_2 = Student(name="Student Two", email="student2@test.com", roll_number="S002", password_hash=hash_password("password123"))

    db_session.add_all([teacher_a, teacher_b, student_1, student_2])
    db_session.commit()
    db_session.refresh(teacher_a)
    db_session.refresh(teacher_b)
    db_session.refresh(student_1)
    db_session.refresh(student_2)

    token_teacher_a = create_access_token({"sub": str(teacher_a.id), "role": "teacher", "email": teacher_a.email})
    token_teacher_b = create_access_token({"sub": str(teacher_b.id), "role": "teacher", "email": teacher_b.email})
    token_student_1 = create_access_token({"sub": str(student_1.id), "role": "student", "email": student_1.email})
    token_student_2 = create_access_token({"sub": str(student_2.id), "role": "student", "email": student_2.email})

    return {
        "teacher_a": teacher_a,
        "teacher_b": teacher_b,
        "student_1": student_1,
        "student_2": student_2,
        "headers_ta": {"Authorization": f"Bearer {token_teacher_a}"},
        "headers_tb": {"Authorization": f"Bearer {token_teacher_b}"},
        "headers_s1": {"Authorization": f"Bearer {token_student_1}"},
        "headers_s2": {"Authorization": f"Bearer {token_student_2}"},
    }


def test_complete_class_exam_access_control(client, auth_setup, db_session):
    h_ta = auth_setup["headers_ta"]
    h_tb = auth_setup["headers_tb"]
    h_s1 = auth_setup["headers_s1"]
    h_s2 = auth_setup["headers_s2"]
    s1_id = auth_setup["student_1"].id
    s2_id = auth_setup["student_2"].id

    # TEST 1: Teacher A creates Class A
    res = client.post("/classes", json={"name": "Physics Class A", "description": "Mechanics"}, headers=h_ta)
    assert res.status_code == 201, res.text
    class_a_id = res.json()["id"]

    # TEST 2: Teacher B creates Class B
    res = client.post("/classes", json={"name": "Chemistry Class B", "description": "Organic"}, headers=h_tb)
    assert res.status_code == 201, res.text
    class_b_id = res.json()["id"]

    # TEST 3: Teacher A cannot access Class B (404/403)
    res = client.get(f"/classes/{class_b_id}", headers=h_ta)
    assert res.status_code in (403, 404), f"Expected 403 or 404, got {res.status_code}"

    res = client.delete(f"/classes/{class_b_id}", headers=h_ta)
    assert res.status_code in (403, 404)

    # TEST 4: Teacher A creates Exam A
    exam_a = Exam(
        title="Physics Midterm",
        teacher_id=auth_setup["teacher_a"].id,
        total_marks=5.0,
    )
    db_session.add(exam_a)
    db_session.commit()
    db_session.refresh(exam_a)
    exam_a_id = exam_a.id

    q1 = Question(
        exam_id=exam_a_id,
        question_text="What is F?",
        question_type="MCQ",
        options='["m*a", "m*v", "m/a", "v/t"]',
        correct_answer="m*a",
        marks=5.0,
    )
    db_session.add(q1)
    db_session.commit()
    db_session.refresh(q1)

    # TEST 5: Teacher B cannot access Exam A
    res = client.get(f"/exams/{exam_a_id}", headers=h_tb)
    assert res.status_code in (403, 404), f"Expected 403 or 404, got {res.status_code}"

    # Enroll Student 1 into Class A
    res = client.post(f"/classes/{class_a_id}/students/{s1_id}", headers=h_ta)
    assert res.status_code == 201, res.text

    # TEST 13: Duplicate enrollment is rejected/prevented (409)
    res_dup = client.post(f"/classes/{class_a_id}/students/{s1_id}", headers=h_ta)
    assert res_dup.status_code == 409, f"Expected 409, got {res_dup.status_code}"

    # TEST 6: Teacher A assigns Exam A to Class A
    res = client.post(f"/exams/{exam_a_id}/assign/{class_a_id}", headers=h_ta)
    assert res.status_code == 201, res.text
    assignment_id = res.json()["id"]

    # TEST 14: Duplicate exam assignment is rejected/prevented (409)
    res_dup_assign = client.post(f"/exams/{exam_a_id}/assign/{class_a_id}", headers=h_ta)
    assert res_dup_assign.status_code == 409, f"Expected 409, got {res_dup_assign.status_code}"

    # TEST 11: Teacher B cannot assign Teacher A's exam to Class B
    res_unauth_assign = client.post(f"/exams/{exam_a_id}/assign/{class_b_id}", headers=h_tb)
    assert res_unauth_assign.status_code in (403, 404), f"Expected 403 or 404, got {res_unauth_assign.status_code}"

    # TEST 12: Teacher A cannot delete Teacher B's exam
    exam_b = Exam(
        title="Chemistry Quiz",
        teacher_id=auth_setup["teacher_b"].id,
    )
    db_session.add(exam_b)
    db_session.commit()
    db_session.refresh(exam_b)
    exam_b_id = exam_b.id

    res_del = client.delete(f"/exams/{exam_b_id}", headers=h_ta)
    assert res_del.status_code in (403, 404), f"Expected 403 or 404, got {res_del.status_code}"

    # TEST 7: Student 1 enrolled in Class A can see Exam A
    res = client.get("/student/exams", headers=h_s1)
    assert res.status_code == 200
    s1_exams = res.json()
    assert any(e["id"] == exam_a_id for e in s1_exams), "Student 1 should see Exam A"

    # Direct access: Student 1 can access Exam A
    res = client.get(f"/exams/{exam_a_id}", headers=h_s1)
    assert res.status_code == 200
    assert res.json()["id"] == exam_a_id

    # TEST 8: Student 2 NOT enrolled in Class A cannot see Exam A
    res = client.get("/student/exams", headers=h_s2)
    assert res.status_code == 200
    s2_exams = res.json()
    assert not any(e["id"] == exam_a_id for e in s2_exams), "Student 2 should NOT see Exam A"

    # TEST 9: Student 2 tries GET /exams/{exam_id} directly -> denied (403 or 404)
    res = client.get(f"/exams/{exam_a_id}", headers=h_s2)
    assert res.status_code in (403, 404), f"Expected 403 or 404, got {res.status_code}"

    # TEST 10: Student 2 tries submitting Exam A directly -> denied (403 or 404)
    submit_payload = {
        "exam_id": exam_a_id,
        "answers": {str(q1.id): "m*a"},
    }
    res = client.post("/submissions/", json=submit_payload, headers=h_s2)
    assert res.status_code in (403, 404), f"Expected 403 or 404, got {res.status_code}"

    # Student 1 submits Exam A -> authorized and successful
    res_s1_sub = client.post("/submissions/", json=submit_payload, headers=h_s1)
    assert res_s1_sub.status_code == 201, res_s1_sub.text
    sub_id = res_s1_sub.json()["id"]

    # Teacher Results Security:
    # Teacher A can view results for Exam A
    res_ta_sub = client.get(f"/submissions/exam/{exam_a_id}", headers=h_ta)
    assert res_ta_sub.status_code == 200
    assert any(s["id"] == sub_id for s in res_ta_sub.json())

    # Teacher B cannot view results for Exam A
    res_tb_sub = client.get(f"/submissions/exam/{exam_a_id}", headers=h_tb)
    assert res_tb_sub.status_code in (403, 404)

    # Class exams endpoint:
    # Teacher A can view exams assigned to Class A
    res_ca_exams = client.get(f"/classes/{class_a_id}/exams", headers=h_ta)
    assert res_ca_exams.status_code == 200
    assert any(e["id"] == exam_a_id for e in res_ca_exams.json())

    # Student 1 can view exams assigned to Class A
    res_s1_ca_exams = client.get(f"/classes/{class_a_id}/exams", headers=h_s1)
    assert res_s1_ca_exams.status_code == 200
    assert any(e["id"] == exam_a_id for e in res_s1_ca_exams.json())

    # Student 2 cannot view exams assigned to Class A (403/404)
    res_s2_ca_exams = client.get(f"/classes/{class_a_id}/exams", headers=h_s2)
    assert res_s2_ca_exams.status_code in (403, 404)
