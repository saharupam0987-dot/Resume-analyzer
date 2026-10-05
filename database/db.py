import sqlite3
import os
from config.settings import DB_PATH


def get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            subject TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            roll_number TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            total_marks REAL DEFAULT 0,
            num_mcq INTEGER DEFAULT 0,
            num_fill_blanks INTEGER DEFAULT 0,
            num_subjective INTEGER DEFAULT 0,
            marks_per_mcq REAL DEFAULT 1.0,
            marks_per_fill REAL DEFAULT 2.0,
            marks_per_subjective REAL DEFAULT 5.0,
            topic_weightage TEXT DEFAULT '{}',
            evaluation_strictness TEXT DEFAULT 'medium',
            collection_name TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (teacher_id) REFERENCES teachers(id)
        );

        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER NOT NULL,
            question_type TEXT NOT NULL,
            question_text TEXT NOT NULL,
            options TEXT DEFAULT '[]',
            correct_answer TEXT DEFAULT '',
            marks REAL DEFAULT 0,
            topic TEXT DEFAULT '',
            difficulty TEXT DEFAULT 'medium',
            question_number INTEGER DEFAULT 0,
            FOREIGN KEY (exam_id) REFERENCES exams(id)
        );

        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            total_score REAL DEFAULT 0,
            max_score REAL DEFAULT 0,
            percentage REAL DEFAULT 0,
            attempt_mode TEXT DEFAULT 'online',
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            evaluated_at TIMESTAMP,
            FOREIGN KEY (exam_id) REFERENCES exams(id),
            FOREIGN KEY (student_id) REFERENCES students(id)
        );

        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            student_answer TEXT DEFAULT '',
            marks_awarded REAL DEFAULT 0,
            max_marks REAL DEFAULT 0,
            feedback TEXT DEFAULT '',
            confidence REAL DEFAULT 0,
            FOREIGN KEY (submission_id) REFERENCES submissions(id),
            FOREIGN KEY (question_id) REFERENCES questions(id)
        );
    """)

    conn.commit()

    # --- Migrations for existing databases ---
    try:
        cursor.execute("ALTER TABLE submissions ADD COLUMN attempt_mode TEXT DEFAULT 'online'")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Column already exists

    conn.close()


# --- Teacher CRUD ---

def create_teacher(name: str, email: str, password_hash: str, subject: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO teachers (name, email, password_hash, subject) VALUES (?, ?, ?, ?)",
        (name, email, password_hash, subject),
    )
    conn.commit()
    teacher_id = cursor.lastrowid
    conn.close()
    return teacher_id


def get_teacher_by_email(email: str) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM teachers WHERE email = ?", (email,)).fetchone()
    conn.close()
    return dict(row) if row else None


# --- Student CRUD ---

def create_student(name: str, email: str, roll_number: str, password_hash: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO students (name, email, roll_number, password_hash) VALUES (?, ?, ?, ?)",
        (name, email, roll_number, password_hash),
    )
    conn.commit()
    student_id = cursor.lastrowid
    conn.close()
    return student_id


def get_student_by_email(email: str) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM students WHERE email = ?", (email,)).fetchone()
    conn.close()
    return dict(row) if row else None


# --- Exam CRUD ---

def create_exam(teacher_id: int, title: str, total_marks: float,
                num_mcq: int, num_fill_blanks: int, num_subjective: int,
                marks_per_mcq: float, marks_per_fill: float, marks_per_subjective: float,
                topic_weightage: str, collection_name: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO exams (teacher_id, title, total_marks, num_mcq, num_fill_blanks,
           num_subjective, marks_per_mcq, marks_per_fill, marks_per_subjective,
           topic_weightage, collection_name)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (teacher_id, title, total_marks, num_mcq, num_fill_blanks,
         num_subjective, marks_per_mcq, marks_per_fill, marks_per_subjective,
         topic_weightage, collection_name),
    )
    conn.commit()
    exam_id = cursor.lastrowid
    conn.close()
    return exam_id


def get_exam(exam_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        """SELECT e.*, t.name as teacher_name, t.subject as teacher_subject
           FROM exams e JOIN teachers t ON e.teacher_id = t.id
           WHERE e.id = ?""",
        (exam_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_exams_by_teacher(teacher_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM exams WHERE teacher_id = ? ORDER BY created_at DESC", (teacher_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_exams() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT e.*, t.name as teacher_name, t.subject as teacher_subject
           FROM exams e JOIN teachers t ON e.teacher_id = t.id
           ORDER BY e.created_at DESC"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_exam_strictness(exam_id: int, strictness: str):
    conn = get_connection()
    conn.execute("UPDATE exams SET evaluation_strictness = ? WHERE id = ?", (strictness, exam_id))
    conn.commit()
    conn.close()


# --- Question CRUD ---

def insert_questions(exam_id: int, questions: list[dict]):
    conn = get_connection()
    cursor = conn.cursor()
    for q in questions:
        cursor.execute(
            """INSERT INTO questions (exam_id, question_type, question_text, options,
               correct_answer, marks, topic, difficulty, question_number)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (exam_id, q["question_type"], q["question_text"], q.get("options", "[]"),
             q["correct_answer"], q["marks"], q.get("topic", ""), q.get("difficulty", "medium"),
             q.get("question_number", 0)),
        )
    conn.commit()
    conn.close()


def get_questions_by_exam(exam_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM questions WHERE exam_id = ? ORDER BY question_number", (exam_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Submission CRUD ---

def create_submission(exam_id: int, student_id: int, attempt_mode: str = "online") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO submissions (exam_id, student_id, status, attempt_mode) VALUES (?, ?, 'submitted', ?)",
        (exam_id, student_id, attempt_mode),
    )
    conn.commit()
    sub_id = cursor.lastrowid
    conn.close()
    return sub_id


def get_submission_by_student_exam(student_id: int, exam_id: int) -> dict | None:
    """Check if a student already has a submission for a given exam."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM submissions WHERE student_id = ? AND exam_id = ?",
        (student_id, exam_id),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_submission(submission_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM submissions WHERE id = ?", (submission_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_submissions_by_exam(exam_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT s.*, st.name as student_name, st.roll_number,
           COALESCE(s.attempt_mode, 'online') as attempt_mode
           FROM submissions s JOIN students st ON s.student_id = st.id
           WHERE s.exam_id = ? ORDER BY s.submitted_at DESC""",
        (exam_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_submissions_by_student(student_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT s.*, e.title as exam_title
           FROM submissions s JOIN exams e ON s.exam_id = e.id
           WHERE s.student_id = ? ORDER BY s.submitted_at DESC""",
        (student_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_submission_scores(submission_id: int, total_score: float, max_score: float, percentage: float):
    conn = get_connection()
    conn.execute(
        """UPDATE submissions SET total_score = ?, max_score = ?, percentage = ?,
           status = 'evaluated', evaluated_at = CURRENT_TIMESTAMP WHERE id = ?""",
        (total_score, max_score, percentage, submission_id),
    )
    conn.commit()
    conn.close()


# --- Answer CRUD ---

def insert_answers(submission_id: int, answers: list[dict]):
    conn = get_connection()
    cursor = conn.cursor()
    for a in answers:
        cursor.execute(
            """INSERT INTO answers (submission_id, question_id, student_answer,
               marks_awarded, max_marks, feedback, confidence)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (submission_id, a["question_id"], a["student_answer"],
             a.get("marks_awarded", 0), a.get("max_marks", 0),
             a.get("feedback", ""), a.get("confidence", 0)),
        )
    conn.commit()
    conn.close()


def get_answers_by_submission(submission_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT a.*, q.question_text, q.question_type, q.correct_answer, q.options
           FROM answers a JOIN questions q ON a.question_id = q.id
           WHERE a.submission_id = ? ORDER BY q.question_number""",
        (submission_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_answer_marks(answer_id: int, marks_awarded: float, feedback: str):
    conn = get_connection()
    conn.execute(
        "UPDATE answers SET marks_awarded = ?, feedback = ? WHERE id = ?",
        (marks_awarded, feedback, answer_id),
    )
    conn.commit()
    conn.close()
