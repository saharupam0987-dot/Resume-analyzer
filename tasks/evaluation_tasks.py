import time
import logging
from datetime import datetime
from tasks.celery_app import celery_app
from tasks.helpers import update_job_status
from api.database import get_task_db_session
from api.models import Submission, Exam, Question
from evaluation.mcq_evaluator import evaluate_mcq
from evaluation.fill_evaluator import evaluate_fill_blank
from evaluation.subjective_evaluator import evaluate_subjective

logger = logging.getLogger("eval_app.tasks.evaluation")


@celery_app.task(
    bind=True,
    name="tasks.evaluation_tasks.evaluate_submission_task",
    autoretry_for=(ConnectionError, TimeoutError),
    max_retries=2,
    retry_backoff=True,
)
def evaluate_submission_task(self, task_job_id: int, submission_id: int) -> dict:
    """Asynchronously evaluate a student submission via Celery background worker.

    Args:
        task_job_id: The database TaskJob ID for progress tracking.
        submission_id: The Submission ID to evaluate.

    Returns:
        Summary dict containing score, percentage, and evaluation status.
    """
    start_time = time.time()
    celery_task_id = self.request.id
    logger.info(f"Starting async evaluation | task_job_id={task_job_id} | submission_id={submission_id}")

    update_job_status(
        task_job_id=task_job_id,
        celery_task_id=celery_task_id,
        status="PROCESSING",
        progress=10,
        message="Loading submission data...",
    )

    with get_task_db_session() as db:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            err_msg = f"Submission id={submission_id} not found."
            logger.error(err_msg)
            update_job_status(task_job_id=task_job_id, status="FAILED", progress=0, error=err_msg)
            raise ValueError(err_msg)

        exam = db.query(Exam).filter(Exam.id == submission.exam_id).first()
        if not exam:
            err_msg = f"Exam id={submission.exam_id} not found."
            logger.error(err_msg)
            update_job_status(task_job_id=task_job_id, status="FAILED", progress=0, error=err_msg)
            raise ValueError(err_msg)

        questions = list(exam.questions)
        total_questions = len(questions)
        answers = submission.answers or {}
        evaluations = {}
        total_score = 0.0
        strictness = exam.evaluation_strictness or "medium"

        update_job_status(
            task_job_id=task_job_id,
            status="PROCESSING",
            progress=25,
            message=f"Evaluating {total_questions} questions...",
        )

        for i, q in enumerate(questions):
            q_id_str = str(q.id)
            student_ans = answers.get(q_id_str)
            if student_ans is None:
                student_ans = answers.get(q.id)
            if student_ans is None:
                student_ans = answers.get(str(q.question_number))
            if student_ans is None:
                student_ans = ""
            student_ans = str(student_ans).strip()

            q_type = (q.question_type or "mcq").lower()
            max_marks = float(q.marks or 1.0)
            correct_ans = q.correct_answer or ""

            res_detail = {}
            if not student_ans:
                marks_awarded = 0.0
                feedback = f"No answer provided. Expected: {correct_ans}" if correct_ans else "No answer provided."
                res_detail = {
                    "score": 0.0,
                    "max_score": max_marks,
                    "percentage": 0.0,
                    "confidence": 1.0,
                    "overall_assessment": "No answer provided",
                    "criteria": [{
                        "criterion": "Response submission",
                        "status": "missing",
                        "score": 0.0,
                        "max_score": max_marks,
                        "feedback": "No answer was provided by the student.",
                    }],
                    "strengths": [],
                    "missing_points": ["Complete answer was not submitted."],
                    "improvement_suggestion": "Please provide an answer explaining the required concepts.",
                    "evaluation_method": "empty_guard",
                }
            elif q_type == "mcq":
                res = evaluate_mcq(student_ans, correct_ans, max_marks)
                marks_awarded = float(res.get("marks_awarded", 0.0))
                feedback = res.get("feedback", "")
                is_full = marks_awarded >= max_marks
                res_detail = {
                    "score": marks_awarded,
                    "max_score": max_marks,
                    "percentage": round((marks_awarded / max_marks) * 100, 1) if max_marks > 0 else 0.0,
                    "confidence": 1.0,
                    "overall_assessment": "Correct option selected" if is_full else "Incorrect option selected",
                    "criteria": [{
                        "criterion": "Correct option selection",
                        "status": "satisfied" if is_full else "incorrect",
                        "score": marks_awarded,
                        "max_score": max_marks,
                        "feedback": feedback,
                    }],
                    "strengths": ["Selected the correct answer choice."] if is_full else [],
                    "missing_points": [f"Correct option: {correct_ans}"] if not is_full else [],
                    "improvement_suggestion": "",
                    "evaluation_method": "rule_based",
                }
            elif q_type in ("fill_blank", "fill_blanks", "fill"):
                res = evaluate_fill_blank(student_ans, correct_ans, max_marks, strictness)
                marks_awarded = float(res.get("marks_awarded", 0.0))
                feedback = res.get("feedback", "")
                is_full = marks_awarded >= max_marks
                res_detail = {
                    "score": marks_awarded,
                    "max_score": max_marks,
                    "percentage": round((marks_awarded / max_marks) * 100, 1) if max_marks > 0 else 0.0,
                    "confidence": float(res.get("confidence", 0.9)),
                    "overall_assessment": "Exact or fuzzy match" if is_full else ("Partially correct" if marks_awarded > 0 else "Incorrect term"),
                    "criteria": [{
                        "criterion": "Accurate term or concept match",
                        "status": "satisfied" if is_full else ("partially_satisfied" if marks_awarded > 0 else "incorrect"),
                        "score": marks_awarded,
                        "max_score": max_marks,
                        "feedback": feedback,
                    }],
                    "strengths": ["Correct term provided."] if is_full else [],
                    "missing_points": [f"Expected term: {correct_ans}"] if not is_full else [],
                    "improvement_suggestion": "",
                    "evaluation_method": "fuzzy_matching",
                }
            elif q_type in ("subjective", "long"):
                res = evaluate_subjective(
                    question_text=q.question_text,
                    student_answer=student_ans,
                    correct_answer=correct_ans,
                    max_marks=max_marks,
                    strictness=strictness,
                    collection_name=exam.collection_name,
                )
                marks_awarded = float(res.get("score", res.get("marks_awarded", 0.0)))
                feedback = res.get("feedback", "")
                res_detail = res
            else:
                marks_awarded = 0.0
                feedback = "Evaluation complete."
                res_detail = {"score": 0.0, "max_score": max_marks, "overall_assessment": "Unknown question type"}

            total_score += marks_awarded
            evaluations[q_id_str] = {
                "question_id": q.id,
                "question_number": q.question_number,
                "question_text": q.question_text,
                "question_type": q.question_type,
                "student_answer": student_ans,
                "correct_answer": correct_ans,
                "marks_awarded": marks_awarded,
                "max_marks": max_marks,
                "feedback": feedback,
                # Structured details
                "score": res_detail.get("score", marks_awarded),
                "percentage": res_detail.get("percentage", round((marks_awarded / max_marks) * 100, 1) if max_marks > 0 else 0.0),
                "confidence": res_detail.get("confidence", 0.9),
                "overall_assessment": res_detail.get("overall_assessment", "Evaluated"),
                "criteria": res_detail.get("criteria", []),
                "strengths": res_detail.get("strengths", []),
                "missing_points": res_detail.get("missing_points", []),
                "improvement_suggestion": res_detail.get("improvement_suggestion", ""),
                "evaluation_method": res_detail.get("evaluation_method", "ai_rubric"),
                "semantic_similarity": res_detail.get("semantic_similarity", None),
            }

            # Update progress incrementally
            progress_pct = int(25 + ((i + 1) / total_questions) * 65)
            update_job_status(task_job_id=task_job_id, progress=progress_pct)

        # Update submission record
        submission.total_score = round(total_score, 1)
        submission.status = "evaluated"
        submission.evaluations = evaluations
        submission.evaluated_at = datetime.utcnow()
        db.commit()

        elapsed = round(time.time() - start_time, 2)
        meta = {
            "submission_id": submission.id,
            "exam_id": exam.id,
            "total_score": round(total_score, 1),
            "questions_evaluated": total_questions,
            "duration_seconds": elapsed,
        }

        update_job_status(
            task_job_id=task_job_id,
            status="COMPLETED",
            progress=100,
            message="Submission evaluation completed successfully",
            result_metadata=meta,
        )

        return {"status": "COMPLETED", "result_metadata": meta}
