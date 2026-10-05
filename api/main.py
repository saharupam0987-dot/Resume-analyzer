import time
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.database import engine, Base
from api.routers import auth, exams, submission, tasks, classes

logger = logging.getLogger("eval_app.api")

# Create tables with retry in case DB is still establishing socket on container startup
for attempt in range(5):
    try:
        Base.metadata.create_all(bind=engine)
        break
    except Exception as e:
        if attempt < 4:
            logger.warning(f"Database connection attempt {attempt + 1} failed: {e}. Retrying in 2s...")
            time.sleep(2)
        else:
            logger.error("Failed to connect to database after multiple attempts.")
            raise e

app = FastAPI(
    title="Student-Teacher Evaluation API",
    version="2.0.0",
    swagger_ui_parameters={"persistAuthorization": True},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(classes.router)
app.include_router(exams.router)
app.include_router(exams.student_exams_router)
app.include_router(submission.router)
app.include_router(tasks.router)


@app.get("/")
def root():
    return {"status": "running", "message": "eval_app API is active and loaded"}


@app.get("/health")
def health():
    return {"status": "healthy", "service": "fastapi"}