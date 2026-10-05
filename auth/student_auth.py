import bcrypt
from database.db import create_student, get_student_by_email


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def register_student(name: str, email: str, roll_number: str, password: str) -> tuple[bool, str]:
    if not all([name, email, roll_number, password]):
        return False, "All fields are required."

    existing = get_student_by_email(email)
    if existing:
        return False, "A student with this email already exists."

    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    pw_hash = hash_password(password)
    student_id = create_student(name, email, roll_number, pw_hash)
    return True, f"Registration successful! Student ID: {student_id}"


def login_student(email: str, password: str) -> tuple[bool, str | dict]:
    if not all([email, password]):
        return False, "Email and password are required."

    student = get_student_by_email(email)
    if not student:
        return False, "No student found with this email."

    if not verify_password(password, student["password_hash"]):
        return False, "Incorrect password."

    return True, student
