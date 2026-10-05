import json
import re
from config.settings import LLM_PROVIDER, GOOGLE_API_KEY, OPENAI_API_KEY, GEMINI_MODEL, OPENAI_MODEL
from generation.prompts import MCQ_PROMPT, FILL_BLANK_PROMPT, SUBJECTIVE_PROMPT


def get_llm_response(prompt: str) -> str:
    """Get a response from the configured LLM provider."""
    if LLM_PROVIDER == "gemini":
        import google.generativeai as genai
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        return response.text
    elif LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model=OPENAI_MODEL, api_key=OPENAI_API_KEY, temperature=0.7)
        response = llm.invoke(prompt)
        return response.content
    else:
        raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")


def parse_json_response(response_text: str) -> list | dict:
    """Parse JSON from LLM response, handling markdown code blocks."""
    text = response_text.strip()
    # Remove markdown code fences if present
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        text = match.group(1).strip()
    return json.loads(text)


def generate_mcqs(context: str, topic: str, count: int, marks_per_q: float) -> list[dict]:
    """Generate MCQ questions using LLM + RAG context."""
    prompt = MCQ_PROMPT.format(context=context, topic=topic, count=count, marks=marks_per_q)
    response = get_llm_response(prompt)
    questions = parse_json_response(response)

    for q in questions:
        q["question_type"] = "mcq"
        q["marks"] = marks_per_q
        q["topic"] = topic
        q["options"] = json.dumps(q.get("options", []))

    return questions[:count]


def generate_fill_blanks(context: str, topic: str, count: int, marks_per_q: float) -> list[dict]:
    """Generate fill-in-the-blank questions using LLM + RAG context."""
    prompt = FILL_BLANK_PROMPT.format(context=context, topic=topic, count=count, marks=marks_per_q)
    response = get_llm_response(prompt)
    questions = parse_json_response(response)

    for q in questions:
        q["question_type"] = "fill_blank"
        q["marks"] = marks_per_q
        q["topic"] = topic
        q["options"] = "[]"

    return questions[:count]


def generate_subjective(context: str, topic: str, count: int, marks_per_q: float) -> list[dict]:
    """Generate subjective questions using LLM + RAG context."""
    prompt = SUBJECTIVE_PROMPT.format(context=context, topic=topic, count=count, marks=marks_per_q)
    response = get_llm_response(prompt)
    questions = parse_json_response(response)

    for q in questions:
        q["question_type"] = "subjective"
        q["marks"] = marks_per_q
        q["topic"] = topic
        q["options"] = "[]"

    return questions[:count]
