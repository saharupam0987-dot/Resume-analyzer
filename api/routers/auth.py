from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from api.database import get_db
from api.models import Teacher, Student
from api.schemas import (
    TeacherRegister,
    StudentRegister,
    LoginRequest,
    TokenResponse,
)
from api.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================================
# TEACHER REGISTRATION
# ============================================================

@router.post(
    "/register/teacher",
    status_code=status.HTTP_201_CREATED
)
def register_teacher(
    data: TeacherRegister,
    db: Session = Depends(get_db)
):
    # Check if email already exists
    existing_teacher = (
        db.query(Teacher)
        .filter(Teacher.email == data.email)
        .first()
    )

    if existing_teacher:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create teacher
    teacher = Teacher(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        subject=data.subject,
    )

    db.add(teacher)

    try:
        db.commit()
        db.refresh(teacher)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    return {
        "message": "Teacher registered successfully"
    }


# ============================================================
# STUDENT REGISTRATION
# ============================================================

@router.post(
    "/register/student",
    status_code=status.HTTP_201_CREATED
)
def register_student(
    data: StudentRegister,
    db: Session = Depends(get_db)
):
    # --------------------------------------------------------
    # Check duplicate email
    # --------------------------------------------------------

    existing_student_email = (
        db.query(Student)
        .filter(Student.email == data.email)
        .first()
    )

    if existing_student_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # --------------------------------------------------------
    # Check duplicate roll number
    # --------------------------------------------------------

    existing_student_roll = (
        db.query(Student)
        .filter(Student.roll_number == data.roll_number)
        .first()
    )

    if existing_student_roll:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Roll number already registered"
        )

    # --------------------------------------------------------
    # Create student
    # --------------------------------------------------------

    student = Student(
        name=data.name,
        email=data.email,
        roll_number=data.roll_number,
        password_hash=hash_password(data.password),
    )

    db.add(student)

    # --------------------------------------------------------
    # Commit safely
    # --------------------------------------------------------

    try:
        db.commit()
        db.refresh(student)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or roll number already registered"
        )

    return {
        "message": "Student registered successfully"
    }


# ============================================================
# LOGIN
# ============================================================

@router.post(
    "/login",
    response_model=TokenResponse
)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    user = None

    # --------------------------------------------------------
    # Find teacher
    # --------------------------------------------------------

    if data.role == "teacher":

        user = (
            db.query(Teacher)
            .filter(Teacher.email == data.email)
            .first()
        )

    # --------------------------------------------------------
    # Find student
    # --------------------------------------------------------

    elif data.role == "student":

        user = (
            db.query(Student)
            .filter(Student.email == data.email)
            .first()
        )

    # --------------------------------------------------------
    # Invalid role
    # --------------------------------------------------------

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role"
        )

    # --------------------------------------------------------
    # Check user/password
    # --------------------------------------------------------

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not verify_password(
        data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # --------------------------------------------------------
    # Create JWT token
    # --------------------------------------------------------

    token = create_access_token(
        {
            "sub": str(user.id),
            "role": data.role,
            "email": user.email,
        }
    )

    # --------------------------------------------------------
    # Return login response
    # --------------------------------------------------------

    return TokenResponse(
        access_token=token,
        role=data.role,
        user_id=user.id,
        name=user.name,
    )

# ============================================================
# SWAGGER / OAUTH2 TOKEN LOGIN
# ============================================================

@router.post("/token")
def login_for_swagger(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    OAuth2-compatible login endpoint for Swagger UI.

    Swagger sends:
        username = email
        password = password
    """

    email = username

    # --------------------------------------------------------
    # Try teacher
    # --------------------------------------------------------

    teacher = (
        db.query(Teacher)
        .filter(Teacher.email == email)
        .first()
    )

    if teacher and verify_password(
        password,
        teacher.password_hash
    ):
        token = create_access_token(
            {
                "sub": str(teacher.id),
                "role": "teacher",
                "email": teacher.email,
            }
        )

        return {
            "access_token": token,
            "token_type": "bearer",
        }

    # --------------------------------------------------------
    # Try student
    # --------------------------------------------------------

    student = (
        db.query(Student)
        .filter(Student.email == email)
        .first()
    )

    if student and verify_password(
        password,
        student.password_hash
    ):
        token = create_access_token(
            {
                "sub": str(student.id),
                "role": "student",
                "email": student.email,
            }
        )

        return {
            "access_token": token,
            "token_type": "bearer",
        }

    # --------------------------------------------------------
    # Invalid credentials
    # --------------------------------------------------------

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )


# ============================================================
# CURRENT USER PROFILE
# ============================================================

@router.get("/me")
def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # --------------------------------------------------------
    # Teacher profile
    # --------------------------------------------------------

    if current_user["role"] == "teacher":

        teacher = (
            db.query(Teacher)
            .filter(Teacher.id == current_user["id"])
            .first()
        )

        if teacher:
            return {
                "id": teacher.id,
                "name": teacher.name,
                "email": teacher.email,
                "role": "teacher",
                "subject": teacher.subject,
            }

    # --------------------------------------------------------
    # Student profile
    # --------------------------------------------------------

    elif current_user["role"] == "student":

        student = (
            db.query(Student)
            .filter(Student.id == current_user["id"])
            .first()
        )

        if student:
            return {
                "id": student.id,
                "name": student.name,
                "email": student.email,
                "role": "student",
                "roll_number": student.roll_number,
            }

    # --------------------------------------------------------
    # User not found
    # --------------------------------------------------------

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )