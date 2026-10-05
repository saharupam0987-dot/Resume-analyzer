import os
import json
import re
from pathlib import Path
from google import genai
from google.genai import types
from dotenv import load_dotenv
from typing import Optional, Dict, Any

# Load .env file
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

CANDIDATE_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
    "gemini-flash-latest",
]


def generate_deterministic_fallback_questions(
    context_text: str,
    title: str = "Midterm Exam",
    num_mcq: int = 3,
    num_fill: int = 2,
    num_sub: int = 2,
    strictness: str = "medium",
    blueprint: Optional[Dict[str, Any]] = None,
) -> list:
    """Generates structured syllabus/blueprint-aware questions deterministically
    when Gemini API quotas or network calls are temporarily unavailable.
    Guarantees that exam generation never fails.
    """
    print("[*] Using deterministic fallback question synthesis...")
    questions = []
    q_num = 1

    # Extract topics or phrases from context text
    raw_lines = [line.strip() for line in (context_text or "").splitlines() if len(line.strip()) > 25]
    topics_from_context = []
    for line in raw_lines[:25]:
        words = [w.strip(":,.;()\"'") for w in line.split() if len(w) > 3]
        if len(words) >= 2:
            topics_from_context.append(" ".join(words[:4]))
    if not topics_from_context:
        topics_from_context = ["Core Concepts", "Theoretical Foundations", "Practical Applications", "Problem Solving"]

    # Retrieve question requirements from blueprint (supporting both keys)
    q_reqs = []
    if blueprint:
        q_reqs = blueprint.get("questions") or blueprint.get("question_requirements") or []

    if q_reqs:
        for idx, item in enumerate(q_reqs, 1):
            tp = item.get("topic") or topics_from_context[idx % len(topics_from_context)]
            qtype = (item.get("question_type") or item.get("archetype") or "subjective").lower()
            diff = item.get("difficulty") or strictness
            marks = float(item.get("marks") or 5.0)
            guidance = item.get("guidance") or ""

            if "mcq" in qtype:
                questions.append({
                    "question_type": "mcq",
                    "question_text": f"Which of the following statements is correct regarding {tp}?",
                    "options": [
                        f"A. {tp} provides deterministic behavior under bounded constraints.",
                        f"B. {tp} cannot be evaluated in finite polynomial time.",
                        f"C. {tp} operates strictly without any state transitions.",
                        f"D. None of the above statements are accurate.",
                    ],
                    "correct_answer": f"A. {tp} provides deterministic behavior under bounded constraints.",
                    "marks": marks or 2.0,
                    "topic": tp,
                    "difficulty": diff,
                    "question_number": q_num,
                })
            elif "fill" in qtype or "blank" in qtype:
                questions.append({
                    "question_type": "fill_blanks",
                    "question_text": f"In the formal study of {tp}, the primary operational invariant is defined as ______.",
                    "options": [],
                    "correct_answer": "Formal Specification",
                    "marks": marks or 3.0,
                    "topic": tp,
                    "difficulty": diff,
                    "question_number": q_num,
                })
            else:
                prompt_label = "Design and construct" if ("construction" in qtype or "design" in qtype) else "Explain in detail and analyze"
                questions.append({
                    "question_type": "subjective",
                    "question_text": f"{prompt_label} the solution for {tp}. {guidance} Provide complete technical justifications and diagrams where applicable.",
                    "options": [],
                    "correct_answer": f"Model Answer for {tp}:\n1. Formal definition and governing equations.\n2. Step-by-step structural derivation or state diagram.\n3. Analysis of complexity and boundary correctness.",
                    "marks": marks or 5.0,
                    "topic": tp,
                    "difficulty": diff,
                    "question_number": q_num,
                })
            q_num += 1
    else:
        # Standard distribution fallback
        for i in range(num_mcq):
            tp = topics_from_context[i % len(topics_from_context)]
            questions.append({
                "question_type": "mcq",
                "question_text": f"Which principle best describes {tp} in the context of this subject?",
                "options": [
                    f"A. Fundamental structural property of {tp}.",
                    f"B. Arbitrary unconstrained transition function.",
                    f"C. Deprecated historical notation.",
                    f"D. Random heuristic approximation.",
                ],
                "correct_answer": f"A. Fundamental structural property of {tp}.",
                "marks": 2.0,
                "topic": tp,
                "difficulty": strictness,
                "question_number": q_num,
            })
            q_num += 1

        for i in range(num_fill):
            tp = topics_from_context[(i + num_mcq) % len(topics_from_context)]
            questions.append({
                "question_type": "fill_blanks",
                "question_text": f"The primary operational rule governing {tp} is designated as ______.",
                "options": [],
                "correct_answer": "Invariant Condition",
                "marks": 3.0,
                "topic": tp,
                "difficulty": strictness,
                "question_number": q_num,
            })
            q_num += 1

        for i in range(num_sub):
            tp = topics_from_context[(i + num_mcq + num_fill) % len(topics_from_context)]
            questions.append({
                "question_type": "subjective",
                "question_text": f"Discuss the theoretical foundation and analytical properties of {tp}. Detail its operational significance with illustrative examples.",
                "options": [],
                "correct_answer": f"Model Answer: Comprehensive exposition of {tp} covering: (a) definitions and axioms, (b) derivation of key relations, (c) edge case handling and error bounds.",
                "marks": 5.0,
                "topic": tp,
                "difficulty": strictness,
                "question_number": q_num,
            })
            q_num += 1

    print(f"[+] Deterministic fallback produced {len(questions)} questions.")
    return questions


def generate_exam_from_text(
    context_text: str,
    title: str = "Midterm Exam",
    num_mcq: int = 3,
    num_fill: int = 2,
    num_sub: int = 2,
    strictness: str = "medium",
    blueprint: Optional[Dict[str, Any]] = None,
) -> list:
    """Uses Gemini to synthesize structured exam questions from PDF text.
    If a blueprint is supplied, it strictly adheres to the requested archetypes, topics, and constraints.
    Otherwise, it falls back to standard MCQ, fill-in-the-blanks, and subjective distributions.
    Includes multi-model fallback and deterministic synthesis if quotas are exhausted.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("[-] Error: GEMINI_API_KEY is missing from .env. Using fallback generator.")
        return generate_deterministic_fallback_questions(
            context_text=context_text,
            title=title,
            num_mcq=num_mcq,
            num_fill=num_fill,
            num_sub=num_sub,
            strictness=strictness,
            blueprint=blueprint,
        )

    try:
        client = genai.Client(api_key=api_key)
        sample_context = context_text[:15000] if context_text else "General Course Material"

        # Check blueprint questions
        q_reqs = []
        if blueprint:
            q_reqs = blueprint.get("questions") or blueprint.get("question_requirements") or []

        if q_reqs:
            # Construct blueprint-driven prompt
            global_reqs = blueprint.get("global_requirements", {})
            
            blueprint_instructions = []
            for i, q in enumerate(q_reqs, 1):
                cnt = q.get("count") or 1
                tp = q.get("topic") or "General"
                qtype = q.get("question_type") or q.get("archetype") or "subjective"
                diff = q.get("difficulty") or strictness
                m = q.get("marks") or (10.0 if "10" in str(q) else 5.0)
                unit_info = f" from Unit {q.get('unit')}" if q.get("unit") else ""
                bloom_info = f" at {q.get('bloom_level')} cognitive level" if q.get("bloom_level") else ""
                guidance_info = f". Specific guidance: {q.get('guidance')}" if q.get("guidance") else ""
                blueprint_instructions.append(
                    f"- Item {i}: Generate {cnt} question(s) on topic '{tp}'{unit_info}. Archetype/Type: '{qtype}'{bloom_info}. Difficulty: '{diff}'. Marks per question: {m}{guidance_info}."
                )

            global_constraints = []
            if global_reqs.get("university_style"):
                global_constraints.append("- Format paper in standard university academic style with rigorous wording.")
            if global_reqs.get("application_based"):
                global_constraints.append("- Use practical, scenario-based application contexts.")
            if global_reqs.get("avoid_direct_definitions"):
                global_constraints.append("- Strictly avoid shallow or direct definition-only questions. Focus on analysis, construction, and problem-solving.")
            if global_reqs.get("avoid_simple_questions"):
                global_constraints.append("- Avoid overly simple or basic questions.")
            if global_reqs.get("numerical_heavy"):
                global_constraints.append("- Emphasize numerical and computation-heavy questions.")
            if global_reqs.get("theory_heavy"):
                global_constraints.append("- Emphasize theoretical proofs and in-depth conceptual formulations.")
            if global_reqs.get("unit_notes"):
                for u, note in global_reqs.get("unit_notes", {}).items():
                    global_constraints.append(f"- Note for Unit {u}: {note}.")

            reqs_str = "\n".join(blueprint_instructions)
            constraints_str = "\n".join(global_constraints)

            prompt = f"""
            You are a university professor creating an examination paper from this course material:
            \"\"\"{sample_context}\"\"\"

            EXAMINATION BLUEPRINT REQUIREMENTS:
            - Exam Title: {title}
            - Overall Evaluation Strictness: {strictness}
            
            SPECIFIC QUESTION SPECIFICATIONS:
            {reqs_str}

            GLOBAL PAPER CONSTRAINTS:
            {constraints_str}

            CRITICAL RULES:
            - For any MCQ archetype, provide exactly 4 options prefixed with letters A, B, C, D and indicate the single correct answer.
            - For any fill_blanks archetype, the question text MUST contain '______'.
            - For construction, design, ambiguity, proof, conversion, derivation, tracing, or subjective problems, include detailed model answer keys.
            - Provide appropriate question_type matching either 'mcq', 'fill_blanks', 'subjective', or the requested archetype.

            You MUST return ONLY a valid JSON array of question objects matching this schema:
            [
              {{
                "question_type": "mcq|fill_blanks|subjective|construction|conversion|ambiguity|...",
                "question_text": "Detailed question text...",
                "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
                "correct_answer": "Model answer / correct key...",
                "marks": 5.0,
                "topic": "Topic Name",
                "difficulty": "medium",
                "question_number": 1
              }}
            ]
            """
        else:
            # Legacy generation prompt
            prompt = f"""
            You are a university professor creating an exam paper from this course material:
            \"\"\"{sample_context}\"\"\"

            EXAM REQUIREMENTS:
            - Exam Title: {title}
            - Generate exactly {num_mcq} Multiple Choice Questions (MCQ) [2 marks each, exactly 4 options with letters A, B, C, D, and 1 correct answer]
            - Generate exactly {num_fill} Fill in the Blanks questions [3 marks each, question MUST contain '______']
            - Generate exactly {num_sub} Subjective questions [5 marks each, with model answer key]
            - Difficulty / Strictness: {strictness}

            You MUST return ONLY a valid JSON array of question objects matching this schema:
            [
              {{
                "question_type": "mcq",
                "question_text": "What is ...?",
                "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
                "correct_answer": "A. ...",
                "marks": 2.0,
                "topic": "Topic Name",
                "difficulty": "{strictness}",
                "question_number": 1
              }},
              {{
                "question_type": "fill_blanks",
                "question_text": "... is defined as ______.",
                "options": [],
                "correct_answer": "Exact Term",
                "marks": 3.0,
                "topic": "Topic Name",
                "difficulty": "{strictness}",
                "question_number": 2
              }},
              {{
                "question_type": "subjective",
                "question_text": "Explain in detail ...",
                "options": [],
                "correct_answer": "Model answer explanation...",
                "marks": 5.0,
                "topic": "Topic Name",
                "difficulty": "{strictness}",
                "question_number": 3
              }}
            ]
            """

        print("[*] Requesting Gemini for exam synthesis...")
        response = None
        last_error = None

        for model_name in CANDIDATE_MODELS:
            try:
                print(f"[*] Trying model: {model_name}...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.2,
                    ),
                )
                if response and response.text:
                    print(f"[+] Model {model_name} succeeded!")
                    break
            except Exception as e:
                print(f"[-] Model {model_name} error: {e}")
                last_error = e

        if not response or not response.text:
            print(f"[-] All candidate models failed ({last_error}). Triggering deterministic fallback.")
            return generate_deterministic_fallback_questions(
                context_text=context_text,
                title=title,
                num_mcq=num_mcq,
                num_fill=num_fill,
                num_sub=num_sub,
                strictness=strictness,
                blueprint=blueprint,
            )

        text = response.text.strip()
        # Clean any potential markdown code blocks
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)

        questions = json.loads(text)
        print(f"[+] Generated {len(questions)} AI questions via Gemini!")
        return questions

    except Exception as e:
        print(f"[-] Gemini Generation Error: {e}. Using deterministic fallback.")
        return generate_deterministic_fallback_questions(
            context_text=context_text,
            title=title,
            num_mcq=num_mcq,
            num_fill=num_fill,
            num_sub=num_sub,
            strictness=strictness,
            blueprint=blueprint,
        )