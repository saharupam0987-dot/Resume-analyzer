import os
import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv

from api.schemas import ExamBlueprint, QuestionRequirement, GlobalRequirements, ParseRequirementsResponse

# Load environment variables
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger("eval_app.generation.requirement_parser")

# Standard supported question archetypes (normalized)
VALID_QUESTION_TYPES = {
    "mcq": "mcq",
    "mcqs": "mcq",
    "multiple choice": "mcq",
    "short answer": "short answer",
    "long answer": "long answer",
    "construction": "construction",
    "design": "design",
    "numerical": "numerical",
    "problem-solving": "problem-solving",
    "problem solving": "problem-solving",
    "application-based": "application-based",
    "application": "application-based",
    "case-based": "case-study",
    "case-study": "case-study",
    "case study": "case-study",
    "proof": "proof",
    "derivation": "derivation",
    "comparison": "comparison",
    "conversion": "conversion",
    "analysis": "analysis",
    "tracing": "tracing",
    "trace": "tracing",
    "execution": "tracing",
    "trace/execution": "tracing",
    "debugging": "debugging",
    "debug": "debugging",
    "explanation": "explanation",
    "explain": "explanation",
    "definition": "definition",
    "justify": "justify/reason",
    "reason": "justify/reason",
    "justify/reason": "justify/reason",
    "ambiguity": "ambiguity",
    "fill in the blank": "fill_blanks",
    "fill_blanks": "fill_blanks",
    "fill in the blanks": "fill_blanks",
}

VALID_DIFFICULTIES = {"easy", "medium", "hard", "mixed"}
VALID_BLOOM_LEVELS = {"remember", "understand", "apply", "analyze", "evaluate", "create"}

PARSER_SYSTEM_PROMPT = """You are an expert academic curriculum and exam blueprint parser.
Your job is ONLY to extract and structure the teacher's natural-language exam requirements into a strict JSON Blueprint.
DO NOT generate exam questions or question text.
DO NOT invent requirements not requested by the teacher.
DO NOT assume unspecified question counts or marks.
Separate individual question requirements from global paper requirements.

DISTINGUISH TOPIC VS QUESTION TYPE:
- Topic is the academic subject matter (e.g., 'DFA', 'NFA to DFA', 'CFG', 'linked lists', 'AVL trees', 'OS scheduling').
- Question type is the cognitive archetype (e.g., 'construction', 'conversion', 'ambiguity', 'MCQ', 'design', 'proof', 'numerical', 'derivation', 'tracing', 'debugging', 'explanation', 'definition', 'short answer', 'long answer').

DIFFICULTY NORMALIZATION:
- 'very tough', 'challenging', 'hard' -> 'hard'
- 'simple', 'basic', 'easy' -> 'easy'
- 'standard', 'moderate', 'medium' -> 'medium'
- 'mix', 'balanced' -> 'mixed'

AMBIGUOUS REQUIREMENTS:
- If a requirement mentions a topic or type without a specific count (e.g. 'Give some difficult questions from DFA', 'Include questions on linked lists'), set "count": null.
- Add an explicit clarification question into the "clarifications" list (e.g., "How many DFA questions should be included?").
- Do NOT make unnecessary clarifications if counts are specified.

OUTPUT FORMAT:
You MUST respond with a single JSON object matching this schema:
{
  "subject": "string or null",
  "total_marks": number or null,
  "duration_minutes": number or null,
  "global_requirements": {
    "difficulty": "easy|medium|hard|mixed",
    "university_style": boolean,
    "application_based": boolean,
    "avoid_direct_definitions": boolean,
    "avoid_simple_questions": boolean,
    "problem_solving": boolean,
    "conceptual": boolean,
    "numerical_heavy": boolean,
    "theory_heavy": boolean,
    "unit_notes": {"unit_key": "instruction"},
    "other_instructions": ["string"]
  },
  "question_requirements": [
    {
      "topic": "string",
      "count": integer or null,
      "question_type": "string or null",
      "difficulty": "easy|medium|hard|mixed or null",
      "marks": number or null,
      "unit": "string or null",
      "bloom_level": "remember|understand|apply|analyze|evaluate|create or null"
    }
  ],
  "clarifications": ["string"]
}
"""


def normalize_question_type(raw_type: Optional[str]) -> Optional[str]:
    if not raw_type:
        return None
    cleaned = raw_type.strip().lower()
    return VALID_QUESTION_TYPES.get(cleaned, cleaned)


def normalize_difficulty(raw_diff: Optional[str]) -> str:
    if not raw_diff:
        return "medium"
    cleaned = raw_diff.strip().lower()
    if cleaned in {"very hard", "tough", "very tough", "difficult", "challenging", "hard"}:
        return "hard"
    if cleaned in {"easy", "simple", "basic"}:
        return "easy"
    if cleaned in {"medium", "moderate", "standard", "normal"}:
        return "medium"
    if cleaned in {"mixed", "balanced", "varied"}:
        return "mixed"
    return "medium"


def rule_based_fallback_parser(
    requirements_text: str,
    subject: Optional[str] = None,
    total_marks: Optional[float] = None,
    duration_minutes: Optional[int] = None,
) -> Tuple[ExamBlueprint, List[str]]:
    """Deterministic heuristic parser used when Gemini is unreachable or for fast offline extraction."""
    text = requirements_text.strip()
    sentences = re.split(r"[.\n;]+", text)

    q_reqs: List[QuestionRequirement] = []
    clarifications: List[str] = []

    global_req = GlobalRequirements()
    lower_text = text.lower()

    # Detect global styles
    if "university" in lower_text or "university-level" in lower_text or "university-style" in lower_text:
        global_req.university_style = True
    if "application" in lower_text or "application-based" in lower_text:
        global_req.application_based = True
    if "avoid direct definition" in lower_text or "avoid direct definitions" in lower_text or "no direct definitions" in lower_text:
        global_req.avoid_direct_definitions = True
    if "avoid simple" in lower_text or "no simple questions" in lower_text:
        global_req.avoid_simple_questions = True
    if "problem solving" in lower_text or "problem-solving" in lower_text:
        global_req.problem_solving = True
    if "conceptual" in lower_text:
        global_req.conceptual = True
    if "numerical-heavy" in lower_text or "numerical heavy" in lower_text:
        global_req.numerical_heavy = True
    if "theory-heavy" in lower_text or "theory heavy" in lower_text:
        global_req.theory_heavy = True

    # Global difficulty
    if "difficult" in lower_text or "tough" in lower_text or "hard" in lower_text:
        global_req.difficulty = "hard"
    elif "easy" in lower_text or "simple" in lower_text:
        global_req.difficulty = "easy"

    # Unit level rules: e.g. "make unit 3 harder", "unit 4 more difficult"
    unit_hard_match = re.search(r"(?:make\s+)?unit\s*(\d+|[ivx]+)\s*(?:harder|more difficult|tougher)", lower_text)
    if unit_hard_match:
        u_id = unit_hard_match.group(1).upper()
        global_req.unit_notes[u_id] = "harder"

    word_num_map = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
    }

    for s in sentences:
        s_clean = s.strip()
        if not s_clean:
            continue
        s_lower = s_clean.lower()

        # Skip purely global statements
        if re.search(r"^(create|make the paper|avoid|ensure|the paper should)", s_lower) and not re.search(r"(question|problem|mcq|give|include)", s_lower):
            continue

        # Extract marks: e.g., "10-mark", "10 mark", "worth 2 marks"
        marks = None
        mark_match = re.search(r"(\d+(?:\.\d+)?)\s*[- ]?marks?", s_lower)
        s_count_target = s_lower
        if mark_match:
            marks = float(mark_match.group(1))
            # Remove the mark phrase so its digit is not mistaken for question count
            s_count_target = s_lower[:mark_match.start()] + s_lower[mark_match.end():]

        # Extract question count from text without marks
        count = None
        count_match = re.search(r"\b(\d+)\s*(?:questions?|problems?|mcqs?)?\b", s_count_target)
        if count_match:
            try:
                count = int(count_match.group(1))
            except ValueError:
                count = None

        if count is None:
            for word, val in word_num_map.items():
                if re.search(rf"\b{word}\b", s_count_target):
                    count = val
                    break

        # Check for vague/ambiguous count (e.g., "some questions", "questions from DFA", "give difficult DFA questions")
        is_ambiguous_count = False
        if count is None and (
            "some" in s_lower or "questions from" in s_lower or "problems from" in s_lower or
            ("give" in s_lower and "questions" in s_lower) or
            ("include" in s_lower and "questions" in s_lower)
        ):
            is_ambiguous_count = True

        # Extract difficulty
        item_diff = None
        if "hard" in s_lower or "difficult" in s_lower or "tough" in s_lower:
            item_diff = "hard"
        elif "easy" in s_lower or "simple" in s_lower:
            item_diff = "easy"
        elif "medium" in s_lower:
            item_diff = "medium"

        # Extract question type / archetype
        q_type = None
        for raw_k, norm_v in VALID_QUESTION_TYPES.items():
            if re.search(rf"\b{re.escape(raw_k)}\b", s_lower):
                q_type = norm_v
                break

        # Extract unit if mentioned in sentence
        unit_match = re.search(r"unit\s*(\d+|[ivx]+)", s_lower)
        unit_val = unit_match.group(1).upper() if unit_match else None

        # Extract topic: Check known subject terms first with word boundary
        topic = None
        for cand_topic in [
            "NFA to DFA", "DFA", "NFA", "CFG", "PDA", "Turing Machine",
            "linked lists", "linked list", "AVL trees", "AVL tree",
            "graph algorithm", "graph algorithms", "binary tree", "binary trees",
            "dynamic programming", "sorting", "operating system scheduling", "deadlock"
        ]:
            if re.search(rf"\b{re.escape(cand_topic.lower())}\b", s_lower):
                topic = cand_topic
                break

        if not topic:
            topic_match = re.search(r"\b(?:from|on|of|involving)\s+([a-zA-Z0-9\s\-]+?)(?:\s+(?:questions?|problems?|mcqs?)|\.|$)", s_clean, re.IGNORECASE)
            if topic_match:
                cand = topic_match.group(1).strip()
                cand = re.sub(r"^(the|a|an|some|difficult|hard|easy)\s+", "", cand, flags=re.IGNORECASE).strip()
                if cand and len(cand) > 1:
                    topic = cand

        # If a question requirement was detected
        if topic or q_type or count or is_ambiguous_count:
            final_topic = topic or (subject or "General")
            req_item = QuestionRequirement(
                topic=final_topic,
                count=count if not is_ambiguous_count else None,
                question_type=q_type,
                difficulty=item_diff or global_req.difficulty or "medium",
                marks=marks,
                unit=unit_val,
            )
            q_reqs.append(req_item)

            if is_ambiguous_count or count is None:
                clarification_text = f"How many {final_topic} questions should be included?"
                if clarification_text not in clarifications:
                    clarifications.append(clarification_text)

    # Subject extraction from first line if "Theory of Computation" or similar mentioned
    detected_subject = subject
    if not detected_subject:
        subj_match = re.search(r"create\s+(?:a\s+)?([a-zA-Z0-9\s]+?)\s+(?:paper|exam)", text, re.IGNORECASE)
        if subj_match:
            detected_subject = subj_match.group(1).strip()

    blueprint = ExamBlueprint(
        subject=detected_subject,
        total_marks=total_marks,
        duration_minutes=duration_minutes,
        global_requirements=global_req,
        question_requirements=q_reqs,
        raw_requirements=text,
    )
    return blueprint, clarifications


def validate_and_normalize_blueprint(
    raw_data: Dict[str, Any],
    fallback_subject: Optional[str] = None,
    fallback_marks: Optional[float] = None,
    fallback_duration: Optional[int] = None,
    raw_requirements: str = "",
) -> Tuple[ExamBlueprint, List[str]]:
    """Validates and strictly normalizes JSON output from Gemini into Pydantic models."""
    clarifications = list(raw_data.get("clarifications") or [])

    # Global requirements
    raw_global = raw_data.get("global_requirements") or {}
    global_req = GlobalRequirements(
        difficulty=normalize_difficulty(raw_global.get("difficulty")),
        university_style=bool(raw_global.get("university_style", False)),
        application_based=bool(raw_global.get("application_based", False)),
        avoid_direct_definitions=bool(raw_global.get("avoid_direct_definitions", False)),
        avoid_simple_questions=bool(raw_global.get("avoid_simple_questions", False)),
        problem_solving=bool(raw_global.get("problem_solving", False)),
        conceptual=bool(raw_global.get("conceptual", False)),
        numerical_heavy=bool(raw_global.get("numerical_heavy", False)),
        theory_heavy=bool(raw_global.get("theory_heavy", False)),
        unit_notes=dict(raw_global.get("unit_notes") or {}),
        other_instructions=list(raw_global.get("other_instructions") or []),
    )

    # Question requirements
    raw_questions = raw_data.get("question_requirements") or raw_data.get("questions") or []
    question_requirements: List[QuestionRequirement] = []

    for q in raw_questions:
        topic = str(q.get("topic") or "General").strip()

        # Count validation (must be positive if present)
        raw_count = q.get("count")
        count = None
        if raw_count is not None:
            try:
                c_val = int(raw_count)
                if c_val > 0:
                    count = c_val
            except (ValueError, TypeError):
                count = None

        if count is None:
            clarification_text = f"How many {topic} questions should be included?"
            if clarification_text not in clarifications:
                clarifications.append(clarification_text)

        # Marks validation
        raw_marks = q.get("marks")
        marks = None
        if raw_marks is not None:
            try:
                m_val = float(raw_marks)
                if m_val > 0:
                    marks = m_val
            except (ValueError, TypeError):
                marks = None

        q_type = normalize_question_type(q.get("question_type") or q.get("type"))
        difficulty = normalize_difficulty(q.get("difficulty") or global_req.difficulty)

        # Unit extraction/normalization
        raw_unit = q.get("unit")
        unit_str = str(raw_unit).strip() if raw_unit is not None else None

        # Bloom taxonomy validation
        raw_bloom = str(q.get("bloom_level") or "").strip().lower()
        bloom_level = raw_bloom if raw_bloom in VALID_BLOOM_LEVELS else None

        req = QuestionRequirement(
            topic=topic,
            count=count,
            question_type=q_type,
            difficulty=difficulty,
            marks=marks,
            unit=unit_str,
            bloom_level=bloom_level,
        )
        question_requirements.append(req)

    # Total marks and duration validation
    subj = raw_data.get("subject") or fallback_subject
    tot_marks = raw_data.get("total_marks") or fallback_marks
    if tot_marks is not None:
        try:
            tot_marks = float(tot_marks)
            if tot_marks <= 0:
                tot_marks = fallback_marks
        except (ValueError, TypeError):
            tot_marks = fallback_marks

    dur = raw_data.get("duration_minutes") or raw_data.get("duration") or fallback_duration
    if dur is not None:
        try:
            dur = int(dur)
            if dur <= 0:
                dur = fallback_duration
        except (ValueError, TypeError):
            dur = fallback_duration

    blueprint = ExamBlueprint(
        subject=subj,
        total_marks=tot_marks,
        duration_minutes=dur,
        global_requirements=global_req,
        question_requirements=question_requirements,
        raw_requirements=raw_requirements,
    )

    return blueprint, clarifications


def parse_exam_requirements(
    requirements: str,
    subject: Optional[str] = None,
    total_marks: Optional[float] = None,
    duration_minutes: Optional[int] = None,
) -> ParseRequirementsResponse:
    """Parses natural-language exam requirements using Gemini structured JSON output,

    with automatic fallback to deterministic heuristic parser if Gemini is unavailable.
    """
    cleaned_requirements = requirements.strip()
    if not cleaned_requirements:
        empty_blueprint = ExamBlueprint(
            subject=subject,
            total_marks=total_marks,
            duration_minutes=duration_minutes,
            global_requirements=GlobalRequirements(),
            question_requirements=[],
            raw_requirements="",
        )
        return ParseRequirementsResponse(blueprint=empty_blueprint, clarifications=[])

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    client = None

    if api_key:
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=api_key)
        except Exception as e:
            logger.warning("Could not initialize google.genai client: %s. Using heuristic parser.", e)

    if client:
        try:
            user_prompt = f"""
            TEACHER PROVIDED CONTEXT:
            Subject: {subject or 'Unspecified'}
            Target Total Marks: {total_marks or 'Unspecified'}
            Target Duration (minutes): {duration_minutes or 'Unspecified'}

            TEACHER NATURAL LANGUAGE REQUIREMENTS:
            \"\"\"{cleaned_requirements}\"\"\"

            Extract and normalize these requirements into the requested structured JSON Exam Blueprint.
            Remember: Return ONLY valid JSON, do NOT generate question contents, and separate topics from question archetypes.
            """

            response_text = None
            candidate_models = ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-flash-latest"]
            for model_name in candidate_models:
                try:
                    logger.info("Calling Gemini model '%s' for requirement parsing...", model_name)
                    response = client.models.generate_content(
                        model=model_name,
                        contents=user_prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=PARSER_SYSTEM_PROMPT,
                            response_mime_type="application/json",
                            temperature=0.1,
                        ),
                    )
                    if response and response.text:
                        response_text = response.text.strip()
                        break
                except Exception as model_err:
                    logger.warning("Gemini model '%s' call failed (%s). Trying next candidate.", model_name, model_err)

            if response_text:
                cleaned_json_str = re.sub(r"^```(?:json)?\s*", "", response_text, flags=re.MULTILINE)
                cleaned_json_str = re.sub(r"\s*```$", "", cleaned_json_str, flags=re.MULTILINE).strip()
                parsed_dict = json.loads(cleaned_json_str)

                blueprint, clarifications = validate_and_normalize_blueprint(
                    raw_data=parsed_dict,
                    fallback_subject=subject,
                    fallback_marks=total_marks,
                    fallback_duration=duration_minutes,
                    raw_requirements=cleaned_requirements,
                )
                return ParseRequirementsResponse(blueprint=blueprint, clarifications=clarifications)

        except Exception as gemini_err:
            logger.error("Gemini requirement parsing failed: %s. Falling back to heuristic parser.", gemini_err)

    # Deterministic fallback parser
    logger.info("Using deterministic fallback parser for requirements...")
    blueprint, clarifications = rule_based_fallback_parser(
        requirements_text=cleaned_requirements,
        subject=subject,
        total_marks=total_marks,
        duration_minutes=duration_minutes,
    )
    return ParseRequirementsResponse(blueprint=blueprint, clarifications=clarifications)
