import os
import json
import pytest
from unittest.mock import patch, MagicMock

from evaluation.subjective_evaluator import (
    evaluate_subjective,
    cosine_similarity,
    _clean_json_response,
    _build_fallback_evaluation,
)

QUESTION = "Explain how James Clear utilized small habits upon entering Denison University to regain control of his life and progress academically and athletically."
REFERENCE_ANSWER = (
    "Clear focused on making tiny, incremental improvements every day. By sticking to consistent routines "
    "like keeping his room tidy and developing disciplined study habits, he regained a sense of control and confidence. "
    "These compounding habits led to stellar academic performance (straight A's) and notable athletic achievements, "
    "culminating in him being named an Academic All-American."
)


# ---------------------------------------------------------------------------
# Test 5: Empty or Whitespace Answer
# ---------------------------------------------------------------------------
def test_empty_or_whitespace_answer():
    """Test 5: Empty answer receives 0 marks, status='missing', and appropriate feedback."""
    res_empty = evaluate_subjective(QUESTION, "", REFERENCE_ANSWER, 5.0)
    assert res_empty["score"] == 0.0
    assert res_empty["marks_awarded"] == 0.0
    assert res_empty["percentage"] == 0.0
    assert res_empty["overall_assessment"] == "No answer provided"
    assert res_empty["criteria"][0]["status"] == "missing"
    assert res_empty["evaluation_method"] == "empty_guard"

    res_spaces = evaluate_subjective(QUESTION, "   \n\t  ", REFERENCE_ANSWER, 5.0)
    assert res_spaces["score"] == 0.0
    assert res_spaces["marks_awarded"] == 0.0
    assert res_spaces["overall_assessment"] == "No answer provided"


# ---------------------------------------------------------------------------
# Test 6: Missing Reference Answer
# ---------------------------------------------------------------------------
def test_missing_reference_answer_handled_safely():
    """Test 6: Missing reference answer does not crash and completes evaluation safely."""
    mock_gemini_resp = {
        "score": 4.0,
        "max_score": 5.0,
        "percentage": 80.0,
        "confidence": 0.85,
        "overall_assessment": "Mostly correct",
        "criteria": [
            {
                "criterion": "Explains core scientific process",
                "status": "satisfied",
                "score": 4.0,
                "max_score": 5.0,
                "feedback": "Correctly describes conversion of light into chemical energy.",
            }
        ],
        "strengths": ["Clear explanation of basic inputs and outputs."],
        "missing_points": ["Could mention chlorophyll role."],
        "improvement_suggestion": "Detail the role of chloroplasts and chlorophyll.",
    }

    with patch("evaluation.subjective_evaluator.genai.Client") as mock_client:
        inst = MagicMock()
        inst.models.generate_content.return_value = MagicMock(text=json.dumps(mock_gemini_resp))
        mock_client.return_value = inst

        res = evaluate_subjective(
            question_text="Explain photosynthesis.",
            student_answer="Plants use sunlight, water, and carbon dioxide to create oxygen and glucose.",
            correct_answer="",  # empty reference answer
            max_marks=5.0,
        )

    assert "score" in res
    assert res["max_score"] == 5.0
    assert res["score"] == 4.0
    assert res["overall_assessment"] == "Mostly correct"
    assert res["evaluation_method"] == "ai_rubric"


# ---------------------------------------------------------------------------
# Test 1: Fully Correct Answer
# ---------------------------------------------------------------------------
def test_fully_correct_answer():
    """Test 1: Fully correct answer receives approximately full marks and satisfied criteria."""
    student_ans = (
        "James Clear utilized small, daily habits such as keeping his dorm room clean and establishing consistent sleep and study schedules. "
        "These incremental micro-habits restored his sense of control and self-belief after his traumatic injury. Over time, these small "
        "disciplines compounded into academic excellence—earning straight A's—and athletic success as a top baseball pitcher, eventually "
        "earning him selection as an Academic All-American."
    )

    mock_resp = {
        "score": 5.0,
        "max_score": 5.0,
        "percentage": 100.0,
        "confidence": 0.95,
        "overall_assessment": "Fully correct",
        "criteria": [
            {"criterion": "Explains use of small consistent habits", "status": "satisfied", "score": 1.0, "max_score": 1.0, "feedback": "Detailed coverage."},
            {"criterion": "Explains gradual compounding improvement", "status": "satisfied", "score": 1.0, "max_score": 1.0, "feedback": "Accurately noted."},
            {"criterion": "Connects habits to regaining control/confidence", "status": "satisfied", "score": 1.0, "max_score": 1.0, "feedback": "Clear connection."},
            {"criterion": "Addresses academic progress (straight A's)", "status": "satisfied", "score": 1.0, "max_score": 1.0, "feedback": "Explicitly stated."},
            {"criterion": "Addresses athletic progress (All-American)", "status": "satisfied", "score": 1.0, "max_score": 1.0, "feedback": "Included with distinction."},
        ],
        "strengths": ["Comprehensive coverage of habits, psychology, academics, and athletics."],
        "missing_points": [],
        "improvement_suggestion": "Excellent response with complete details.",
    }

    with patch("evaluation.subjective_evaluator.genai.Client") as mock_client:
        inst = MagicMock()
        inst.models.generate_content.return_value = MagicMock(text=json.dumps(mock_resp))
        mock_client.return_value = inst

        res = evaluate_subjective(QUESTION, student_ans, REFERENCE_ANSWER, 5.0)

    assert res["score"] == 5.0
    assert res["percentage"] == 100.0
    assert res["overall_assessment"] == "Fully correct"
    assert len(res["criteria"]) == 5
    assert all(c["status"] == "satisfied" for c in res["criteria"])
    assert len(res["strengths"]) > 0


# ---------------------------------------------------------------------------
# Test 4: Different Wording with Same Meaning (Conceptual Equivalence)
# ---------------------------------------------------------------------------
def test_different_wording_same_meaning():
    """Test 4: Different wording with identical meaning receives full/high marks."""
    student_ans = (
        "Rather than attempting immediate monumental transformations, he concentrated on making tiny changes consistently each day. "
        "Simple everyday disciplines allowed him to rebuild his self-assurance and regain mastery over his routine. This compounding "
        "behavior ultimately propelled him to top collegiate grades and premier athletic honors on the college baseball roster."
    )

    mock_resp = {
        "score": 4.5,
        "max_score": 5.0,
        "percentage": 90.0,
        "confidence": 0.92,
        "overall_assessment": "Mostly correct",
        "criteria": [
            {"criterion": "Explains small incremental changes", "status": "satisfied", "score": 1.0, "max_score": 1.0, "feedback": "Conceptually identical despite distinct phrasing."},
            {"criterion": "Explains regaining control and confidence", "status": "satisfied", "score": 1.0, "max_score": 1.0, "feedback": "Expressed clearly as regaining mastery."},
            {"criterion": "Explains academic and athletic compounding", "status": "satisfied", "score": 1.0, "max_score": 1.0, "feedback": "Covered collegiate grades and athletic honors."},
            {"criterion": "Specific factual details", "status": "partially_satisfied", "score": 0.5, "max_score": 1.0, "feedback": "Could name Denison University or Academic All-American explicitly."},
        ],
        "strengths": ["Superb conceptual grasp of compounding micro-habits."],
        "missing_points": ["Specific naming of the Academic All-American distinction."],
        "improvement_suggestion": "Include proper nouns like Academic All-American.",
    }

    with patch("evaluation.subjective_evaluator.genai.Client") as mock_client:
        inst = MagicMock()
        inst.models.generate_content.return_value = MagicMock(text=json.dumps(mock_resp))
        mock_client.return_value = inst

        res = evaluate_subjective(QUESTION, student_ans, REFERENCE_ANSWER, 5.0)

    # Conceptual equivalence must receive high marks
    assert res["score"] >= 4.0
    assert res["percentage"] >= 80.0
    assert res["overall_assessment"] in ("Mostly correct", "Fully correct")


# ---------------------------------------------------------------------------
# Test 2: Partially Correct Answer
# ---------------------------------------------------------------------------
def test_partially_correct_answer():
    """Test 2: Partially correct answer receives partial marks and highlights missing criteria."""
    student_ans = "He started making small habits every day which helped him feel more confident and in control of his daily life."

    mock_resp = {
        "score": 2.5,
        "max_score": 5.0,
        "percentage": 50.0,
        "confidence": 0.90,
        "overall_assessment": "Partially correct",
        "criteria": [
            {"criterion": "Explains small habits", "status": "satisfied", "score": 1.0, "max_score": 1.0, "feedback": "Correctly mentions small daily habits."},
            {"criterion": "Regaining confidence/control", "status": "satisfied", "score": 1.0, "max_score": 1.0, "feedback": "Correctly notes regaining control."},
            {"criterion": "Academic progress", "status": "missing", "score": 0.0, "max_score": 1.5, "feedback": "Omits academic results."},
            {"criterion": "Athletic progress", "status": "missing", "score": 0.0, "max_score": 1.5, "feedback": "Omits athletic outcomes."},
        ],
        "strengths": ["Identifies the psychological benefit of micro-habits."],
        "missing_points": ["Academic achievements (straight A's)", "Athletic achievements (Academic All-American)"],
        "improvement_suggestion": "Address both the academic and athletic outcomes resulting from these habits.",
    }

    with patch("evaluation.subjective_evaluator.genai.Client") as mock_client:
        inst = MagicMock()
        inst.models.generate_content.return_value = MagicMock(text=json.dumps(mock_resp))
        mock_client.return_value = inst

        res = evaluate_subjective(QUESTION, student_ans, REFERENCE_ANSWER, 5.0)

    assert 2.0 <= res["score"] <= 3.0
    assert res["percentage"] == 50.0
    assert res["overall_assessment"] == "Partially correct"
    assert len(res["missing_points"]) >= 1


# ---------------------------------------------------------------------------
# Test 3: Incorrect or Irrelevant Answer
# ---------------------------------------------------------------------------
def test_incorrect_irrelevant_answer():
    """Test 3: Incorrect or irrelevant answer receives low/zero marks."""
    student_ans = "He built a rocket ship to travel to Mars and study alien civilizations."

    mock_resp = {
        "score": 0.0,
        "max_score": 5.0,
        "percentage": 0.0,
        "confidence": 0.98,
        "overall_assessment": "Incorrect/Irrelevant",
        "criteria": [
            {"criterion": "Relevance to question", "status": "incorrect", "score": 0.0, "max_score": 2.5, "feedback": "Completely irrelevant content."},
            {"criterion": "Factual accuracy to source", "status": "incorrect", "score": 0.0, "max_score": 2.5, "feedback": "Hallucinated / fictional claims."},
        ],
        "strengths": [],
        "missing_points": ["Core concepts of habit formation, Denison University, academics, and athletics."],
        "improvement_suggestion": "Focus directly on the course material and James Clear's actual experience.",
    }

    with patch("evaluation.subjective_evaluator.genai.Client") as mock_client:
        inst = MagicMock()
        inst.models.generate_content.return_value = MagicMock(text=json.dumps(mock_resp))
        mock_client.return_value = inst

        res = evaluate_subjective(QUESTION, student_ans, REFERENCE_ANSWER, 5.0)

    assert res["score"] == 0.0
    assert res["percentage"] == 0.0
    assert res["overall_assessment"] == "Incorrect/Irrelevant"


# ---------------------------------------------------------------------------
# Test 7: Gemini Malformed Response Handled Gracefully
# ---------------------------------------------------------------------------
def test_gemini_malformed_response_handled():
    """Test 7: Malformed Gemini JSON triggers safe semantic fallback without application failure."""
    with patch("evaluation.subjective_evaluator.genai.Client") as mock_client:
        inst = MagicMock()
        inst.models.generate_content.return_value = MagicMock(
            text="Sorry, here is the grade: { unclosed json ... "
        )
        mock_client.return_value = inst

        res = evaluate_subjective(
            QUESTION,
            "He focused on tiny daily habits to rebuild his self-discipline and progress academically.",
            REFERENCE_ANSWER,
            5.0,
        )

    # Must fall back gracefully to structured semantic fallback
    assert res["evaluation_method"] == "semantic_fallback"
    assert res["score"] > 0.0
    assert res["max_score"] == 5.0
    assert isinstance(res["criteria"], list)
    assert len(res["criteria"]) > 0
    assert "overall_assessment" in res


# ---------------------------------------------------------------------------
# Test 8: Gemini API Failure / Timeout Handled Gracefully
# ---------------------------------------------------------------------------
def test_gemini_api_failure_fallback():
    """Test 8: Complete Gemini API network error or timeout executes semantic fallback cleanly."""
    with patch("evaluation.subjective_evaluator.genai.Client") as mock_client:
        inst = MagicMock()
        inst.models.generate_content.side_effect = ConnectionError("Connection refused to Gemini API")
        mock_client.return_value = inst

        res = evaluate_subjective(
            QUESTION,
            "Clear focused on small improvements every day to regain control over his academic studies.",
            REFERENCE_ANSWER,
            5.0,
        )

    assert res["evaluation_method"] == "semantic_fallback"
    assert res["score"] > 0.0
    assert res["max_score"] == 5.0
    assert isinstance(res["criteria"], list)
    assert isinstance(res["strengths"], list)
    assert isinstance(res["missing_points"], list)
    assert "%" not in str(res["score"])  # Clean numeric score
    assert res["semantic_similarity"] is not None
    assert isinstance(res["semantic_similarity"], float)


# ---------------------------------------------------------------------------
# Semantic Similarity Helper Tests
# ---------------------------------------------------------------------------
def test_cosine_similarity_edge_cases():
    """Cosine similarity handles zero vectors and orthogonal vectors safely."""
    assert cosine_similarity([0.0, 0.0], [0.0, 0.0]) == 0.0
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_clean_json_response_markdown():
    """Helper properly extracts JSON content from markdown code fences."""
    raw = "```json\n{\"score\": 4.0}\n```"
    assert _clean_json_response(raw) == "{\"score\": 4.0}"

    raw_plain = "  {\"score\": 4.5}  "
    assert _clean_json_response(raw_plain) == "{\"score\": 4.5}"


# ---------------------------------------------------------------------------
# Live Gemini Integration Test (Executed only if API key present)
# ---------------------------------------------------------------------------
@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set")
def test_live_gemini_evaluation_integration():
    """Integration test verifying live Gemini returns the structured rubric format."""
    student_ans = (
        "Clear started with tiny habits like making his bed and keeping his room tidy. "
        "This gave him a feeling of control, and consistent study habits helped him earn straight A's."
    )
    res = evaluate_subjective(QUESTION, student_ans, REFERENCE_ANSWER, 5.0)

    assert res["max_score"] == 5.0
    assert 0.0 <= res["score"] <= 5.0
    assert isinstance(res["criteria"], list)
    assert len(res["criteria"]) >= 1
    assert "overall_assessment" in res
    assert res["evaluation_method"] in ("ai_rubric", "semantic_fallback")
