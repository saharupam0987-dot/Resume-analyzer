import bcrypt
from database.db import create_teacher, get_teacher_by_email


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def register_teacher(name: str, email: str, password: str, subject: str) -> tuple[bool, str]:
    if not all([name, email, password, subject]):
        return False, "All fields are required."

    existing = get_teacher_by_email(email)
    if existing:
        return False, "A teacher with this email already exists."

    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    pw_hash = hash_password(password)
    teacher_id = create_teacher(name, email, pw_hash, subject)
    return True, f"Registration successful! Teacher ID: {teacher_id}"


def login_teacher(email: str, password: str) -> tuple[bool, str | dict]:
    if not all([email, password]):
        return False, "Email and password are required."

    teacher = get_teacher_by_email(email)
    if not teacher:
        return False, "No teacher found with this email."

    if not verify_password(password, teacher["password_hash"]):
        return False, "Incorrect password."

    return True, teacher
