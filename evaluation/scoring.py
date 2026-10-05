from evaluation.mcq_evaluator import evaluate_mcq
from evaluation.fill_evaluator import evaluate_fill_blank
from evaluation.subjective_evaluator import evaluate_subjective
from database.db import (
    get_questions_by_exam, get_exam, insert_answers,
    update_submission_scores, get_answers_by_submission,
)


def evaluate_submission(submission_id: int, exam_id: int,
                        student_answers: dict[int, str]) -> dict:
    """Evaluate a complete student submission.

    Args:
        submission_id: The submission ID.
        exam_id: The exam ID.
        student_answers: Dict mapping question_id to student's answer string.

    Returns:
        Dict with total_score, max_score, percentage, answers breakdown.
    """
    exam = get_exam(exam_id)
    questions = get_questions_by_exam(exam_id)
    strictness = exam["evaluation_strictness"]

    answer_records = []
    total_score = 0.0
    max_score = 0.0

    for q in questions:
        q_id = q["id"]
        student_answer = student_answers.get(q_id, "")
        q_type = q["question_type"]
        correct = q["correct_answer"]
        marks = q["marks"]

        if q_type == "mcq":
            result = evaluate_mcq(student_answer, correct, marks)
        elif q_type == "fill_blank":
            result = evaluate_fill_blank(student_answer, correct, marks, strictness)
        elif q_type == "subjective":
            result = evaluate_subjective(
                q["question_text"], student_answer, correct, marks, strictness
            )
        else:
            result = {"marks_awarded": 0, "feedback": "Unknown question type.", "confidence": 0}

        answer_records.append({
            "question_id": q_id,
            "student_answer": student_answer,
            "marks_awarded": result["marks_awarded"],
            "max_marks": marks,
            "feedback": result["feedback"],
            "confidence": result.get("confidence", 0),
        })

        total_score += result["marks_awarded"]
        max_score += marks

    # Save answers to DB
    insert_answers(submission_id, answer_records)

    # Update submission scores
    percentage = (total_score / max_score * 100) if max_score > 0 else 0
    update_submission_scores(submission_id, total_score, max_score, round(percentage, 2))

    return {
        "total_score": total_score,
        "max_score": max_score,
        "percentage": round(percentage, 2),
        "answers": answer_records,
    }
