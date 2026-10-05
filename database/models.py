from dataclasses import dataclass, field
from typing import Optional
import json


@dataclass
class Teacher:
    id: Optional[int] = None
    name: str = ""
    email: str = ""
    password_hash: str = ""
    subject: str = ""
    created_at: str = ""


@dataclass
class Student:
    id: Optional[int] = None
    name: str = ""
    email: str = ""
    roll_number: str = ""
    password_hash: str = ""
    created_at: str = ""


@dataclass
class Exam:
    id: Optional[int] = None
    teacher_id: int = 0
    title: str = ""
    total_marks: float = 0.0
    num_mcq: int = 0
    num_fill_blanks: int = 0
    num_subjective: int = 0
    marks_per_mcq: float = 1.0
    marks_per_fill: float = 2.0
    marks_per_subjective: float = 5.0
    topic_weightage: str = "{}"  # JSON string
    evaluation_strictness: str = "medium"  # easy / medium / hard
    collection_name: str = ""  # ChromaDB collection
    created_at: str = ""

    def get_topic_weightage(self) -> dict:
        return json.loads(self.topic_weightage)

    def set_topic_weightage(self, weightage: dict):
        self.topic_weightage = json.dumps(weightage)


@dataclass
class Question:
    id: Optional[int] = None
    exam_id: int = 0
    question_type: str = ""  # mcq / fill_blank / subjective
    question_text: str = ""
    options: str = "[]"  # JSON list for MCQ options
    correct_answer: str = ""
    marks: float = 0.0
    topic: str = ""
    difficulty: str = "medium"
    question_number: int = 0

    def get_options(self) -> list:
        return json.loads(self.options)

    def set_options(self, opts: list):
        self.options = json.dumps(opts)


@dataclass
class Submission:
    id: Optional[int] = None
    exam_id: int = 0
    student_id: int = 0
    status: str = "pending"  # pending / submitted / evaluated
    total_score: float = 0.0
    max_score: float = 0.0
    percentage: float = 0.0
    submitted_at: str = ""
    evaluated_at: str = ""


@dataclass
class Answer:
    id: Optional[int] = None
    submission_id: int = 0
    question_id: int = 0
    student_answer: str = ""
    marks_awarded: float = 0.0
    max_marks: float = 0.0
    feedback: str = ""
    confidence: float = 0.0
