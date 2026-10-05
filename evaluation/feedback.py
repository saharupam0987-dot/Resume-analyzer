from database.db import get_answers_by_submission, get_submission, get_exam


def generate_submission_report(submission_id: int) -> dict:
    """Generate a detailed report for a student's submission.

    Args:
        submission_id: The submission ID.

    Returns:
        Dict with submission info and per-question breakdown.
    """
    submission = get_submission(submission_id)
    if not submission:
        return {"error": "Submission not found."}

    exam = get_exam(submission["exam_id"])
    answers = get_answers_by_submission(submission_id)

    # Categorize by question type
    mcq_answers = [a for a in answers if a["question_type"] == "mcq"]
    fill_answers = [a for a in answers if a["question_type"] == "fill_blank"]
    subjective_answers = [a for a in answers if a["question_type"] == "subjective"]

    # Per-type scores
    def type_score(answers_list):
        awarded = sum(a["marks_awarded"] for a in answers_list)
        total = sum(a["max_marks"] for a in answers_list)
        return awarded, total

    mcq_scored, mcq_total = type_score(mcq_answers)
    fill_scored, fill_total = type_score(fill_answers)
    sub_scored, sub_total = type_score(subjective_answers)

    return {
        "exam_title": exam["title"] if exam else "Unknown",
        "total_score": submission["total_score"],
        "max_score": submission["max_score"],
        "percentage": submission["percentage"],
        "status": submission["status"],
        "submitted_at": submission["submitted_at"],
        "evaluated_at": submission["evaluated_at"],
        "section_scores": {
            "MCQ": {"scored": mcq_scored, "total": mcq_total},
            "Fill in the Blanks": {"scored": fill_scored, "total": fill_total},
            "Subjective": {"scored": sub_scored, "total": sub_total},
        },
        "answers": answers,
    }
