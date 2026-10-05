def evaluate_mcq(student_answer: str, correct_answer: str, max_marks: float) -> dict:
    """Evaluate an MCQ answer by exact match.

    Args:
        student_answer: The student's selected option (e.g., "A", "B").
        correct_answer: The correct option letter.
        max_marks: Maximum marks for this question.

    Returns:
        Dict with marks_awarded, feedback, confidence.
    """
    student_clean = student_answer.strip().upper()[:1]
    correct_clean = correct_answer.strip().upper()[:1]

    if student_clean == correct_clean:
        return {
            "marks_awarded": max_marks,
            "feedback": f"Correct! The answer is {correct_clean}.",
            "confidence": 1.0,
        }
    else:
        return {
            "marks_awarded": 0.0,
            "feedback": f"Incorrect. You answered {student_clean}, the correct answer is {correct_clean}.",
            "confidence": 1.0,
        }
