import pytest
from unittest.mock import patch, MagicMock
from generation.requirement_parser import (
    parse_exam_requirements,
    rule_based_fallback_parser,
    validate_and_normalize_blueprint,
    normalize_difficulty,
    normalize_question_type,
)


# ==============================================================================
# TESTS 1 - 6: Direct Requirement Parser Heuristic / Fallback Engine
# ==============================================================================

def test_1_mcq_linked_lists_heuristic():
    """TEST 1: 'Give 2 MCQs from linked lists.' -> topic: linked lists, count: 2, type: MCQ"""
    text = "Give 2 MCQs from linked lists."
    blueprint, clarifications = rule_based_fallback_parser(text)

    assert len(blueprint.question_requirements) >= 1
    q = blueprint.question_requirements[0]
    assert "linked list" in q.topic.lower()
    assert q.count == 2
    assert q.question_type.lower() == "mcq"


def test_2_dfa_construction_heuristic():
    """TEST 2: 'Give one hard DFA construction problem.' -> topic: DFA, count: 1, difficulty: hard, type: construction"""
    text = "Give one hard DFA construction problem."
    blueprint, clarifications = rule_based_fallback_parser(text)

    assert len(blueprint.question_requirements) >= 1
    q = blueprint.question_requirements[0]
    assert "dfa" in q.topic.lower()
    assert q.count == 1
    assert q.difficulty == "hard"
    assert q.question_type.lower() == "construction"


def test_3_cfg_ambiguity_10_marks_heuristic():
    """TEST 3: 'Give one 10-mark CFG ambiguity question.' -> topic: CFG, count: 1, marks: 10, type: ambiguity"""
    text = "Give one 10-mark CFG ambiguity question."
    blueprint, clarifications = rule_based_fallback_parser(text)

    assert len(blueprint.question_requirements) >= 1
    q = blueprint.question_requirements[0]
    assert "cfg" in q.topic.lower()
    assert q.count == 1
    assert q.marks == 10.0
    assert q.question_type.lower() == "ambiguity"


def test_4_unit_3_and_avoid_direct_definitions_heuristic():
    """TEST 4: 'Make Unit 3 harder and avoid direct definitions.' -> unit: 3, difficulty: hard, avoid_direct_definitions: true"""
    text = "Make Unit 3 harder and avoid direct definitions."
    blueprint, clarifications = rule_based_fallback_parser(text)

    assert blueprint.global_requirements.avoid_direct_definitions is True
    assert blueprint.global_requirements.difficulty == "hard" or "3" in blueprint.global_requirements.unit_notes


def test_5_university_style_and_application_heuristic():
    """TEST 5: 'Make the paper university style and application based.' -> university_style: true, application_based: true"""
    text = "Make the paper university style and application based."
    blueprint, clarifications = rule_based_fallback_parser(text)

    assert blueprint.global_requirements.university_style is True
    assert blueprint.global_requirements.application_based is True


def test_6_ambiguous_dfa_questions_heuristic():
    """TEST 6: 'Give some difficult DFA questions.' -> difficulty: hard, count may remain unspecified, clarification requested"""
    text = "Give some difficult DFA questions."
    blueprint, clarifications = rule_based_fallback_parser(text)

    assert len(blueprint.question_requirements) >= 1
    q = blueprint.question_requirements[0]
    assert "dfa" in q.topic.lower()
    assert q.difficulty == "hard"
    assert q.count is None
    assert len(clarifications) >= 1
    assert any("dfa" in c.lower() for c in clarifications)


# ==============================================================================
# TESTS 1 - 6: Gemini Structured Parser Pipeline with Mocked LLM responses
# ==============================================================================

def test_gemini_structured_parsing_full_pipeline():
    """Verifies that parse_exam_requirements processes Gemini JSON structured output correctly."""
    mock_gemini_json = """
    {
      "subject": "Theory of Computation",
      "total_marks": 100,
      "duration_minutes": 180,
      "global_requirements": {
        "difficulty": "hard",
        "university_style": true,
        "application_based": true,
        "avoid_direct_definitions": true
      },
      "question_requirements": [
        {
          "topic": "DFA",
          "count": 2,
          "question_type": "construction",
          "difficulty": "medium"
        },
        {
          "topic": "NFA to DFA",
          "count": 1,
          "question_type": "conversion",
          "difficulty": "hard"
        },
        {
          "topic": "CFG",
          "count": 1,
          "marks": 10,
          "question_type": "ambiguity",
          "difficulty": "hard"
        }
      ],
      "clarifications": []
    }
    """
    mock_resp = MagicMock()
    mock_resp.text = mock_gemini_json

    with patch("generation.requirement_parser.os.getenv", return_value="fake_key"):
        with patch("google.genai.Client") as MockClient:
            mock_client_instance = MockClient.return_value
            mock_client_instance.models.generate_content.return_value = mock_resp

            resp = parse_exam_requirements(
                requirements="Give 2 DFA construction questions, 1 NFA to DFA conversion, and one 10-mark CFG ambiguity question.",
                subject="Theory of Computation",
                total_marks=100.0,
                duration_minutes=180,
            )

            bp = resp.blueprint
            assert bp.subject == "Theory of Computation"
            assert bp.total_marks == 100.0
            assert bp.duration_minutes == 180
            assert bp.global_requirements.university_style is True
            assert bp.global_requirements.avoid_direct_definitions is True
            assert len(bp.question_requirements) == 3

            q1 = bp.question_requirements[0]
            assert q1.topic == "DFA"
            assert q1.count == 2
            assert q1.question_type == "construction"
            assert q1.difficulty == "medium"

            q2 = bp.question_requirements[1]
            assert q2.topic == "NFA to DFA"
            assert q2.count == 1
            assert q2.question_type == "conversion"
            assert q2.difficulty == "hard"

            q3 = bp.question_requirements[2]
            assert q3.topic == "CFG"
            assert q3.count == 1
            assert q3.marks == 10.0
            assert q3.question_type == "ambiguity"


def test_normalization_and_validation():
    """Test normalization of archetypes, difficulties, and schema validation."""
    assert normalize_difficulty("very tough") == "hard"
    assert normalize_difficulty("challenging") == "hard"
    assert normalize_difficulty("simple") == "easy"
    assert normalize_difficulty("standard") == "medium"
    assert normalize_difficulty("balanced") == "mixed"

    assert normalize_question_type("Multiple Choice") == "mcq"
    assert normalize_question_type("trace/execution") == "tracing"
    assert normalize_question_type("debugging") == "debugging"

    raw_data = {
        "subject": "Theory of Computation",
        "total_marks": -50,  # Invalid, should fall back
        "global_requirements": {
            "difficulty": "very tough",
            "university_style": True,
        },
        "questions": [
            {
                "topic": "PDA",
                "count": -2,  # Invalid count, should be None
                "type": "design",
                "marks": -10,  # Invalid marks, should be None
            }
        ]
    }
    bp, cl = validate_and_normalize_blueprint(raw_data, fallback_marks=100.0)
    assert bp.subject == "Theory of Computation"
    assert bp.total_marks == 100.0
    assert bp.global_requirements.difficulty == "hard"
    assert bp.global_requirements.university_style is True
    assert bp.question_requirements[0].count is None
    assert bp.question_requirements[0].marks is None
    assert bp.question_requirements[0].question_type == "design"
    assert len(cl) >= 1
