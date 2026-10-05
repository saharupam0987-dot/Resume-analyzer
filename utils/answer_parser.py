import io
import json
import tempfile
import os

from config.settings import LLM_PROVIDER, GOOGLE_API_KEY, OPENAI_API_KEY, OPENAI_MODEL
from generation.question_generator import get_llm_response, parse_json_response


def extract_text_from_answer_sheet(uploaded_file) -> str:
    """Extract text from an uploaded answer sheet PDF.

    First tries pdfplumber for typed/digital PDFs.
    If extracted text is too short (< 20 chars), falls back to vision-based
    extraction (Gemini vision or OpenAI vision depending on provider).

    Args:
        uploaded_file: Streamlit UploadedFile object (PDF).

    Returns:
        Extracted text as a string.
    """
    import pdfplumber

    # Read file bytes once so we can reuse them
    file_bytes = uploaded_file.read()
    uploaded_file.seek(0)

    # Attempt 1: pdfplumber for typed PDFs
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    text = "\n\n".join(text_parts).strip()

    if len(text) >= 20:
        return text

    # Attempt 2: Vision-based extraction for handwritten/scanned PDFs
    if LLM_PROVIDER == "gemini":
        return _extract_with_gemini_vision(file_bytes)
    else:
        return _extract_with_openai_vision(file_bytes)


def _extract_with_gemini_vision(file_bytes: bytes) -> str:
    """Use Gemini vision to extract text from a scanned/handwritten PDF."""
    import google.generativeai as genai

    genai.configure(api_key=GOOGLE_API_KEY)

    # Write bytes to a temp file so we can upload it
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        uploaded = genai.upload_file(tmp_path, mime_type="application/pdf")
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content([
            "Extract ALL handwritten or printed text from this document. "
            "Preserve the question numbers (Q1, Q2, etc.) and the answers exactly as written. "
            "Return only the extracted text, nothing else.",
            uploaded,
        ])
        return response.text.strip()
    finally:
        os.unlink(tmp_path)


def _extract_with_openai_vision(file_bytes: bytes) -> str:
    """Use OpenAI vision to extract text from a scanned/handwritten PDF."""
    import base64
    from pdf2image import convert_from_bytes
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)

    # Convert PDF pages to images
    images = convert_from_bytes(file_bytes, dpi=200)

    all_text = []
    for i, img in enumerate(images):
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Extract ALL handwritten or printed text from this image. "
                            "Preserve question numbers (Q1, Q2, etc.) and answers exactly as written. "
                            "Return only the extracted text."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64}"},
                    },
                ],
            }],
            max_tokens=2000,
        )
        page_text = response.choices[0].message.content.strip()
        if page_text:
            all_text.append(page_text)

    return "\n\n".join(all_text)


def parse_answers_from_text(raw_text: str, questions: list[dict]) -> dict[int, str]:
    """Parse student answers from extracted text using LLM.

    Args:
        raw_text: Raw text extracted from the answer sheet.
        questions: List of question dicts from DB (with id, question_number,
                   question_type, question_text).

    Returns:
        Dict mapping question_id (int) to answer string — same format
        that evaluate_submission() expects.
    """
    # Build question list for the prompt
    q_list = []
    for q in questions:
        q_list.append(
            f"  Q{q['question_number']} (type: {q['question_type']}): {q['question_text'][:150]}"
        )
    questions_str = "\n".join(q_list)

    prompt = f"""You are an answer-sheet parser. Given raw text extracted from a student's answer sheet
and the list of questions, extract the student's answer for each question.

QUESTIONS:
{questions_str}

STUDENT'S RAW TEXT:
\"\"\"
{raw_text}
\"\"\"

Return a JSON object mapping question numbers to answers.
For MCQs, return just the option letter (A, B, C, or D).
For fill-in-the-blanks, return the word or phrase.
For subjective questions, return the full answer text.
If a question was not answered, use an empty string.

Return ONLY valid JSON in this exact format (no extra text):
{{"1": "answer for Q1", "2": "answer for Q2", ...}}"""

    response = get_llm_response(prompt)
    parsed = parse_json_response(response)

    # Build mapping from question_number -> question_id
    num_to_id = {str(q["question_number"]): q["id"] for q in questions}

    # Convert question_number keys to question_id keys
    result = {}
    for q_num_str, answer in parsed.items():
        q_id = num_to_id.get(str(q_num_str))
        if q_id is not None:
            result[q_id] = str(answer) if answer else ""

    return result
