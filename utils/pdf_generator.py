import json
import io
from fpdf import FPDF


def generate_question_paper_pdf(exam: dict, questions: list[dict],
                                teacher_name: str, teacher_subject: str) -> bytes:
    """Generate a formatted question paper PDF.

    Args:
        exam: Exam dict from DB (with title, total_marks, etc.).
        questions: List of question dicts from DB.
        teacher_name: Name of the teacher who created the exam.
        teacher_subject: Subject of the teacher.

    Returns:
        PDF file content as bytes.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # --- Header ---
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, exam["title"], new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Teacher: {teacher_name}  |  Subject: {teacher_subject}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(0, 7, f"Total Marks: {exam['total_marks']}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)

    # --- Instructions ---
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Instructions:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    instructions = [
        "1. Write your answers on a separate sheet (typed or handwritten).",
        "2. Prefix each answer with the question number (e.g., Q1: your answer).",
        "3. For MCQs, write the option letter (e.g., Q1: A).",
        "4. For fill-in-the-blanks, write the word/phrase (e.g., Q5: photosynthesis).",
        "5. Save your answer sheet as a PDF and upload it on the platform.",
    ]
    for line in instructions:
        pdf.cell(0, 6, line, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # Divider
    pdf.set_draw_color(0, 0, 0)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    # Separate questions by type
    mcqs = [q for q in questions if q["question_type"] == "mcq"]
    fills = [q for q in questions if q["question_type"] == "fill_blank"]
    subs = [q for q in questions if q["question_type"] == "subjective"]

    # --- Section A: MCQs ---
    if mcqs:
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 9, "Section A: Multiple Choice Questions", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        for q in mcqs:
            _write_question(pdf, q)
            options = q.get("options", "[]")
            if isinstance(options, str):
                options = json.loads(options)
            for opt in options:
                pdf.set_font("Helvetica", "", 10)
                pdf.cell(10)  # indent
                pdf.cell(0, 6, _safe_text(opt), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)

    # --- Section B: Fill in the Blanks ---
    if fills:
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 9, "Section B: Fill in the Blanks", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        for q in fills:
            _write_question(pdf, q)
            pdf.ln(2)

    # --- Section C: Subjective Questions ---
    if subs:
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 9, "Section C: Subjective Questions", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        for q in subs:
            _write_question(pdf, q)
            pdf.ln(3)

    # Output as bytes
    buf = io.BytesIO()
    pdf.output(buf)
    buf.seek(0)
    return buf.getvalue()


def _write_question(pdf: FPDF, q: dict):
    """Write a single question line to the PDF."""
    q_num = q.get("question_number", "")
    marks = q.get("marks", 0)
    text = f"Q{q_num}. {q['question_text']}  [{marks} marks]"
    pdf.set_font("Helvetica", "B", 10)
    # Use multi_cell for long questions that might wrap
    pdf.multi_cell(0, 6, _safe_text(text))


def _safe_text(text: str) -> str:
    """Replace characters that fpdf2 can't encode in latin-1."""
    return text.encode("latin-1", errors="replace").decode("latin-1")
