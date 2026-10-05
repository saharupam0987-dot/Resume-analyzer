import os
import re
import json
import logging
from typing import Dict, Any, List, Optional
import numpy as np

from google import genai
from google.genai import types
from rapidfuzz import fuzz

from rag.embeddings import embed_single
from rag.vector_store import query_collection

logger = logging.getLogger("eval_app.evaluation.subjective")


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Compute cosine similarity between two embedding vectors."""
    a = np.array(vec1, dtype=float)
    b = np.array(vec2, dtype=float)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def _clean_json_response(raw_text: str) -> str:
    """Clean markdown code blocks and whitespace from JSON response."""
    text = raw_text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        text = match.group(1).strip()
    return text


def _extract_fallback_criteria(reference_answer: str) -> List[str]:
    """Break a reference answer into distinct conceptual key points for fallback evaluation."""
    raw_sentences = re.split(r"(?<=[.!?])\s+|\n+", reference_answer.strip())
    criteria = [s.strip() for s in raw_sentences if len(s.strip()) > 15]
    if not criteria:
        criteria = [reference_answer.strip() if reference_answer.strip() else "Core concept coverage"]
    return criteria[:5]


def _build_fallback_evaluation(
    question_text: str,
    student_answer: str,
    correct_answer: str,
    max_marks: float,
    semantic_sim: float,
) -> Dict[str, Any]:
    """Build a structured evaluation when Gemini is unavailable, using semantic similarity & concept matching.
    
    This preserves vector embeddings/similarity search as the conceptual signal while still providing
    a structured rubric response rather than a raw, unrounded percentage dump.
    """
    key_points = _extract_fallback_criteria(correct_answer)
    num_points = max(1, len(key_points))
    mark_per_point = max_marks / float(num_points)

    criteria_list = []
    strengths = []
    missing_points = []
    total_score = 0.0

    student_lower = student_answer.lower()
    student_emb = None
    try:
        student_emb = embed_single(student_answer)
    except Exception as e:
        logger.warning(f"Could not embed student answer in fallback: {e}")

    for point in key_points:
        point_sim = 0.0
        # 1. Semantic similarity per point
        if student_emb:
            try:
                point_emb = embed_single(point)
                point_sim = max(0.0, cosine_similarity(student_emb, point_emb))
            except Exception:
                point_sim = 0.0

        # 2. Token overlap ratio as complementary signal
        token_ratio = fuzz.token_set_ratio(student_lower, point.lower()) / 100.0
        combined_signal = max(point_sim, (token_ratio * 0.7) + (semantic_sim * 0.3))

        if combined_signal >= 0.70:
            status = "satisfied"
            score = mark_per_point
            feedback = f"Addresses concept: '{point[:60]}...' with strong alignment."
            strengths.append(f"Satisfactorily covered: {point[:80]}")
        elif combined_signal >= 0.45:
            status = "partially_satisfied"
            score = round(mark_per_point * 0.5, 1)
            feedback = f"Partially touches upon: '{point[:60]}...' but lacks full detail."
            missing_points.append(f"Needs deeper detail on: {point[:80]}")
        else:
            status = "missing"
            score = 0.0
            feedback = f"Missing key requirement: '{point[:60]}...'"
            missing_points.append(point[:80])

        total_score += score
        criteria_list.append({
            "criterion": point,
            "status": status,
            "score": round(score, 1),
            "max_score": round(mark_per_point, 1),
            "feedback": feedback,
        })

    total_score = round(min(max_marks, max(0.0, total_score)), 1)
    pct = round((total_score / max_marks) * 100, 1) if max_marks > 0 else 0.0

    if pct >= 85:
        assessment = "Fully correct"
    elif pct >= 65:
        assessment = "Mostly correct"
    elif pct >= 40:
        assessment = "Partially correct"
    elif pct > 0:
        assessment = "Limited understanding"
    else:
        assessment = "Incorrect or missing"

    rounded_sim = round(semantic_sim * 100, 1)
    suggestion = "Review the model key points and integrate more specific concepts from the text."

    return {
        "score": total_score,
        "max_score": max_marks,
        "percentage": pct,
        "confidence": round(semantic_sim, 2),
        "overall_assessment": assessment,
        "criteria": criteria_list,
        "strengths": strengths if strengths else ["Attempted response to the question."],
        "missing_points": missing_points,
        "improvement_suggestion": suggestion,
        "evaluation_method": "semantic_fallback",
        "semantic_similarity": round(semantic_sim, 2),
        # Legacy fields for backward compatibility
        "marks_awarded": total_score,
        "feedback": f"{assessment}: Semantic conceptual match ({rounded_sim}%). {suggestion}",
    }


def evaluate_subjective(
    question_text: str,
    student_answer: str,
    correct_answer: str,
    max_marks: float,
    strictness: str = "medium",
    collection_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Evaluates a subjective student response against reference answer and dynamic rubrics.

    Workflow:
    1. Pre-processing & Edge case guards (empty, blank).
    2. Vector Embedding & Semantic Similarity (SentenceTransformer cosine similarity preserved).
    3. ChromaDB vector search retrieval for additional context chunks (if collection exists).
    4. Structured Gemini Rubric Evaluation (conceptual equivalence, criteria grading, strengths, gaps).
    5. Fallback gracefully to semantic rubric evaluation if Gemini is unavailable.
    """
    cleaned_student = str(student_answer or "").strip()
    cleaned_reference = str(correct_answer or "").strip()
    max_marks = float(max_marks or 5.0)

    # Edge Case 1: Empty or whitespace-only response
    if not cleaned_student:
        return {
            "score": 0.0,
            "max_score": max_marks,
            "percentage": 0.0,
            "confidence": 1.0,
            "overall_assessment": "No answer provided",
            "criteria": [
                {
                    "criterion": "Response submission",
                    "status": "missing",
                    "score": 0.0,
                    "max_score": max_marks,
                    "feedback": "No answer was provided by the student.",
                }
            ],
            "strengths": [],
            "missing_points": ["Complete answer was not submitted."],
            "improvement_suggestion": "Please provide an answer explaining the required concepts.",
            "evaluation_method": "empty_guard",
            "semantic_similarity": 0.0,
            "marks_awarded": 0.0,
            "feedback": f"No answer provided. Expected: {cleaned_reference}" if cleaned_reference else "No answer provided.",
        }

    # Step 1: Compute Semantic Similarity using SentenceTransformer (Preserved Requirement)
    semantic_sim = 0.0
    try:
        student_emb = embed_single(cleaned_student)
        if cleaned_reference:
            ref_emb = embed_single(cleaned_reference)
            semantic_sim = max(0.0, cosine_similarity(student_emb, ref_emb))
    except Exception as e:
        logger.warning(f"Error computing SentenceTransformer embeddings: {e}")
        # Secondary fallback for similarity
        if cleaned_reference:
            semantic_sim = (fuzz.token_set_ratio(cleaned_student.lower(), cleaned_reference.lower()) / 100.0)

    # Step 2: Retrieve ChromaDB context chunks if available
    extra_context = ""
    if collection_name:
        try:
            chunks = query_collection(collection_name, cleaned_student, n_results=2)
            if chunks:
                extra_context = "\n---\n".join([c.get("text", "") for c in chunks if c.get("text")])
        except Exception as e:
            logger.debug(f"ChromaDB retrieval skipped: {e}")

    # Edge Case 2: Missing reference answer
    if not cleaned_reference:
        # Evaluate based on question text alone
        cleaned_reference = f"A comprehensive, factually accurate answer to: {question_text}"

    # Step 3: Structured Gemini Rubric Evaluation
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            model_name = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

            system_instruction = (
                "You are an expert academic examiner. You evaluate student subjective answers "
                "using structured, conceptual rubrics rather than surface-level textual matching."
            )

            context_section = f"RELEVANT COURSE MATERIAL CONTEXT:\n{extra_context}" if extra_context else ""

            prompt = f"""
QUESTION:
{question_text}

REFERENCE / MODEL ANSWER:
{cleaned_reference}

{context_section}

STUDENT'S SUBMITTED ANSWER:
{cleaned_student}

MAXIMUM MARKS:
{max_marks}

EVALUATION STRICTNESS:
{strictness} (easy = generous partial credit; medium = balanced conceptual rigor; hard = strict factual completeness)

COMPUTED SEMANTIC SIMILARITY SIGNAL:
{round(semantic_sim * 100, 1)}% alignment with reference embedding.

INSTRUCTIONS:
1. Identify 3 to 6 dynamic, specific rubric criteria based on the question and reference answer.
   Criteria should cover: key concepts, important facts, required points, conceptual understanding, completeness, and explanation quality.
2. CRITICAL - CONCEPTUAL EQUIVALENCE:
   Different wording with the same meaning MUST receive full credit. Do NOT penalize students for using synonyms or alternative sentence structures.
   Example: "Clear focused on small improvements every day" is functionally identical to "He concentrated on making tiny changes consistently instead of trying to transform everything immediately".
3. Leniency: Do NOT penalize for minor spelling or grammar mistakes unless the meaning is genuinely incomprehensible.
4. Anti-Fluff: Do NOT reward answers merely because they are long. Look for substantive conceptual alignment.
5. For each criterion:
   - status: "satisfied" (full score), "partially_satisfied" (partial score), "missing" (0), or "incorrect" (0)
   - score: numeric points awarded for this criterion
   - max_score: numeric maximum points for this criterion
   - feedback: 1 clear sentence explaining why credit was given or deducted
6. Calculate final score = sum of criteria scores (normalized to exactly match maximum marks: {max_marks}).
7. Determine overall_assessment: "Fully correct" | "Mostly correct" | "Partially correct" | "Limited understanding" | "Incorrect/Irrelevant"

Return ONLY a valid JSON object matching this exact schema:
{{
  "score": <float between 0.0 and {max_marks}>,
  "max_score": {max_marks},
  "percentage": <float between 0.0 and 100.0>,
  "confidence": <float between 0.0 and 1.0>,
  "overall_assessment": "<Overall assessment phrase>",
  "criteria": [
    {{
      "criterion": "<Short description of key point/concept>",
      "status": "satisfied|partially_satisfied|missing|incorrect",
      "score": <float>,
      "max_score": <float>,
      "feedback": "<Brief justification>"
    }}
  ],
  "strengths": [
    "<Specific concept student explained well>"
  ],
  "missing_points": [
    "<Specific required concept missing from answer>"
  ],
  "improvement_suggestion": "<1-2 actionable sentences on how to improve>"
}}
"""

            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )

            raw_text = response.text or ""
            clean_text = _clean_json_response(raw_text)
            data = json.loads(clean_text)

            # Validate and normalize scores
            parsed_score = float(data.get("score", 0.0))
            clamped_score = max(0.0, min(parsed_score, max_marks))
            clamped_score = round(clamped_score, 1)

            pct = float(data.get("percentage", (clamped_score / max_marks) * 100 if max_marks > 0 else 0.0))
            pct = round(max(0.0, min(100.0, pct)), 1)

            criteria_data = data.get("criteria", [])
            normalized_criteria = []
            for c in criteria_data:
                c_score = float(c.get("score", 0.0))
                c_max = float(c.get("max_score", 1.0))
                normalized_criteria.append({
                    "criterion": str(c.get("criterion", "Concept requirement")),
                    "status": str(c.get("status", "satisfied")).lower(),
                    "score": round(c_score, 1),
                    "max_score": round(c_max, 1),
                    "feedback": str(c.get("feedback", "")),
                })

            strengths = [str(s) for s in data.get("strengths", []) if str(s).strip()]
            missing_points = [str(m) for m in data.get("missing_points", []) if str(m).strip()]
            suggestion = str(data.get("improvement_suggestion", "")).strip()
            overall_assessment = str(data.get("overall_assessment", "Evaluated")).strip()
            confidence = float(data.get("confidence", 0.9))

            # Concise summary feedback string for backward compatibility
            first_strength = strengths[0] if strengths else ""
            concise_feedback = f"{overall_assessment}. {suggestion or first_strength}".strip()

            return {
                "score": clamped_score,
                "max_score": max_marks,
                "percentage": pct,
                "confidence": round(confidence, 2),
                "overall_assessment": overall_assessment,
                "criteria": normalized_criteria,
                "strengths": strengths,
                "missing_points": missing_points,
                "improvement_suggestion": suggestion,
                "evaluation_method": "ai_rubric",
                "semantic_similarity": round(semantic_sim, 2),
                # Legacy compatibility fields
                "marks_awarded": clamped_score,
                "feedback": concise_feedback,
            }

        except Exception as e:
            logger.error(f"Gemini AI rubric evaluation failed: {e}. Executing semantic fallback.", exc_info=True)

    # Step 4: Semantic Fallback Evaluation (Preserved SentenceTransformer & Concept Matching)
    return _build_fallback_evaluation(
        question_text=question_text,
        student_answer=cleaned_student,
        correct_answer=cleaned_reference,
        max_marks=max_marks,
        semantic_sim=semantic_sim,
    )
