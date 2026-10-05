from rapidfuzz import fuzz
from config.settings import STRICTNESS_THRESHOLDS


def evaluate_fill_blank(student_answer: str, correct_answer: str,
                        max_marks: float, strictness: str = "medium") -> dict:
    """Evaluate a fill-in-the-blank answer using fuzzy string matching.

    Args:
        student_answer: The student's answer.
        correct_answer: The correct answer.
        max_marks: Maximum marks for this question.
        strictness: Evaluation strictness level.

    Returns:
        Dict with marks_awarded, feedback, confidence.
    """
    student_clean = student_answer.strip().lower()
    correct_clean = correct_answer.strip().lower()

    if not student_clean:
        return {
            "marks_awarded": 0.0,
            "feedback": f"No answer provided. The correct answer is: {correct_answer}",
            "confidence": 1.0,
        }

    # Exact match
    if student_clean == correct_clean:
        return {
            "marks_awarded": max_marks,
            "feedback": "Correct!",
            "confidence": 1.0,
        }

    # Fuzzy matching
    ratio = fuzz.ratio(student_clean, correct_clean)
    partial_ratio = fuzz.partial_ratio(student_clean, correct_clean)
    token_sort = fuzz.token_sort_ratio(student_clean, correct_clean)

    best_score = max(ratio, partial_ratio, token_sort)
    threshold = STRICTNESS_THRESHOLDS[strictness]["fill_blank_threshold"]

    if best_score >= threshold:
        # Scale marks based on how close the match is
        marks = max_marks * (best_score / 100.0)
        marks = round(marks * 2) / 2  # Round to nearest 0.5
        return {
            "marks_awarded": min(marks, max_marks),
            "feedback": f"Close match (score: {best_score}%). Expected: {correct_answer}",
            "confidence": best_score / 100.0,
        }
    else:
        return {
            "marks_awarded": 0.0,
            "feedback": f"Incorrect. Your answer: '{student_answer}'. Expected: '{correct_answer}' (match: {best_score}%).",
            "confidence": 1.0 - (best_score / 100.0),
        }
