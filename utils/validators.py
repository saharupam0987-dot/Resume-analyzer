import re


def validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_weightage(weightage: dict) -> tuple[bool, str]:
    """Validate that topic weightages sum to 100."""
    if not weightage:
        return False, "At least one topic is required."

    total = sum(weightage.values())
    if abs(total - 100) > 0.01:
        return False, f"Topic weightages must sum to 100%. Current sum: {total}%"

    for topic, weight in weightage.items():
        if weight <= 0:
            return False, f"Topic '{topic}' has invalid weight: {weight}"

    return True, "Valid"


def validate_marks_distribution(num_mcq: int, num_fill: int, num_subjective: int,
                                marks_mcq: float, marks_fill: float, marks_sub: float,
                                total_marks: float) -> tuple[bool, str]:
    """Validate that marks distribution matches total marks."""
    calculated = (num_mcq * marks_mcq) + (num_fill * marks_fill) + (num_subjective * marks_sub)
    if abs(calculated - total_marks) > 0.01:
        return False, (
            f"Marks don't add up. "
            f"MCQ: {num_mcq}x{marks_mcq}={num_mcq*marks_mcq}, "
            f"Fill: {num_fill}x{marks_fill}={num_fill*marks_fill}, "
            f"Subjective: {num_subjective}x{marks_sub}={num_subjective*marks_sub} "
            f"= {calculated}. Expected: {total_marks}"
        )
    return True, "Valid"
