import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import api.database
from api.database import Base, get_db
from api.main import app
from api.models import Teacher, TaskJob
from api.security import hash_password, create_access_token
from tasks.celery_app import celery_app

# Use isolated SQLite database for testing
TEST_DB_PATH = Path(__file__).resolve().parent / "test_eval.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Patch SessionLocal and engine in api.database so get_task_db_session uses test_engine
api.database.engine = test_engine
api.database.SessionLocal = TestingSessionLocal


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except Exception:
            pass


@pytest.fixture
def db_session():
    """Provides an isolated DB session that rolls back after each test."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(autouse=True)
def override_db_dependency():
    """Overrides get_db in FastAPI to use the test database."""
    def _get_test_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def teacher_auth_headers(db_session):
    """Creates a teacher user and returns valid Bearer token headers."""
    teacher = db_session.query(Teacher).filter(Teacher.email == "test_teacher@test.com").first()
    if not teacher:
        teacher = Teacher(
            name="Test Teacher",
            email="test_teacher@test.com",
            password_hash=hash_password("Teacher@123"),
            subject="Computer Science",
        )
        db_session.add(teacher)
        db_session.commit()
        db_session.refresh(teacher)

    token = create_access_token({"sub": str(teacher.id), "role": "teacher", "email": teacher.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def configure_celery_eager():
    """Configure Celery to run in eager mode for testing (no live broker required)."""
    original_eager = celery_app.conf.task_always_eager
    original_propagates = celery_app.conf.task_eager_propagates
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    yield
    celery_app.conf.task_always_eager = original_eager
    celery_app.conf.task_eager_propagates = original_propagates
