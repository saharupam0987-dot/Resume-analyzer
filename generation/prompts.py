MCQ_PROMPT = """You are an expert exam question generator. Based on the following context from course material, generate exactly {count} Multiple Choice Questions (MCQs) on the topic "{topic}".

CONTEXT:
{context}

REQUIREMENTS:
- Each question must be directly based on the provided context
- Each question must have exactly 4 options labeled A, B, C, D
- Exactly one option must be correct
- Wrong options (distractors) should be plausible but clearly incorrect
- Questions should vary in difficulty
- Each question is worth {marks} mark(s)

OUTPUT FORMAT (strict JSON array):
[
  {{
    "question_text": "The question here?",
    "options": ["A) option1", "B) option2", "C) option3", "D) option4"],
    "correct_answer": "A",
    "difficulty": "easy|medium|hard"
  }}
]

Generate exactly {count} MCQs. Return ONLY the JSON array, no other text."""


FILL_BLANK_PROMPT = """You are an expert exam question generator. Based on the following context from course material, generate exactly {count} Fill-in-the-Blank questions on the topic "{topic}".

CONTEXT:
{context}

REQUIREMENTS:
- Each question must be directly based on the provided context
- Use "______" to indicate the blank
- The answer should be a single word or short phrase (max 3-4 words)
- Questions should test key concepts and definitions
- Each question is worth {marks} mark(s)

OUTPUT FORMAT (strict JSON array):
[
  {{
    "question_text": "The ______ is the process of converting data into a coded format.",
    "correct_answer": "encryption",
    "difficulty": "easy|medium|hard"
  }}
]

Generate exactly {count} Fill-in-the-Blank questions. Return ONLY the JSON array, no other text."""


SUBJECTIVE_PROMPT = """You are an expert exam question generator. Based on the following context from course material, generate exactly {count} subjective/descriptive questions on the topic "{topic}".

CONTEXT:
{context}

REQUIREMENTS:
- Each question must be directly based on the provided context
- Questions should require detailed explanations (3-10 sentences)
- Include a mix of "Explain", "Describe", "Compare", "Analyze" type questions
- Each question is worth {marks} mark(s)
- Also provide a model answer for each question that covers all key points

OUTPUT FORMAT (strict JSON array):
[
  {{
    "question_text": "Explain the concept of X and its significance in Y.",
    "correct_answer": "Model answer: X is defined as... It is significant because...",
    "difficulty": "easy|medium|hard"
  }}
]

Generate exactly {count} subjective questions. Return ONLY the JSON array, no other text."""


EVALUATION_PROMPT = """You are an expert answer evaluator. Evaluate the student's answer against the model answer.

QUESTION: {question}
MODEL ANSWER: {model_answer}
STUDENT ANSWER: {student_answer}
MAXIMUM MARKS: {max_marks}
EVALUATION STRICTNESS: {strictness}

STRICTNESS GUIDELINES:
- Easy: Be lenient. Accept answers that capture the core idea even if wording differs. Give generous partial credit.
- Medium: Balanced evaluation. Key concepts must be present. Reasonable partial credit for partially correct answers.
- Hard: Strict evaluation. Answer must be accurate, complete, and well-structured. Minimal partial credit.

Evaluate the answer and respond in this exact JSON format:
{{
  "marks_awarded": <number between 0 and {max_marks}>,
  "confidence": <number between 0.0 and 1.0>,
  "feedback": "Brief feedback explaining the grade (2-3 sentences)"
}}

Return ONLY the JSON object, no other text."""
