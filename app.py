import streamlit as st
from database.db import init_db

# Initialize database on first run
init_db()

st.set_page_config(
    page_title="Student-Teacher Evaluation System",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_type" not in st.session_state:
    st.session_state.user_type = None
if "user_data" not in st.session_state:
    st.session_state.user_data = None


def logout():
    st.session_state.logged_in = False
    st.session_state.user_type = None
    st.session_state.user_data = None


def show_login_page():
    st.title("Student-Teacher Evaluation System")
    st.markdown("---")

    tab_teacher, tab_student = st.tabs(["Teacher", "Student"])

    with tab_teacher:
        teacher_tab_login, teacher_tab_register = st.tabs(["Login", "Register"])

        with teacher_tab_login:
            st.subheader("Teacher Login")
            with st.form("teacher_login_form"):
                email = st.text_input("Email", key="tl_email")
                password = st.text_input("Password", type="password", key="tl_pass")
                submitted = st.form_submit_button("Login")
                if submitted:
                    from auth.teacher_auth import login_teacher
                    success, result = login_teacher(email, password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.user_type = "teacher"
                        st.session_state.user_data = result
                        st.rerun()
                    else:
                        st.error(result)

        with teacher_tab_register:
            st.subheader("Teacher Registration")
            with st.form("teacher_register_form"):
                name = st.text_input("Full Name", key="tr_name")
                email = st.text_input("Email", key="tr_email")
                subject = st.text_input("Subject", key="tr_subject")
                password = st.text_input("Password", type="password", key="tr_pass")
                confirm = st.text_input("Confirm Password", type="password", key="tr_confirm")
                submitted = st.form_submit_button("Register")
                if submitted:
                    if password != confirm:
                        st.error("Passwords do not match.")
                    else:
                        from auth.teacher_auth import register_teacher
                        success, msg = register_teacher(name, email, password, subject)
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)

    with tab_student:
        student_tab_login, student_tab_register = st.tabs(["Login", "Register"])

        with student_tab_login:
            st.subheader("Student Login")
            with st.form("student_login_form"):
                email = st.text_input("Email", key="sl_email")
                password = st.text_input("Password", type="password", key="sl_pass")
                submitted = st.form_submit_button("Login")
                if submitted:
                    from auth.student_auth import login_student
                    success, result = login_student(email, password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.user_type = "student"
                        st.session_state.user_data = result
                        st.rerun()
                    else:
                        st.error(result)

        with student_tab_register:
            st.subheader("Student Registration")
            with st.form("student_register_form"):
                name = st.text_input("Full Name", key="sr_name")
                email = st.text_input("Email", key="sr_email")
                roll = st.text_input("Roll Number", key="sr_roll")
                password = st.text_input("Password", type="password", key="sr_pass")
                confirm = st.text_input("Confirm Password", type="password", key="sr_confirm")
                submitted = st.form_submit_button("Register")
                if submitted:
                    if password != confirm:
                        st.error("Passwords do not match.")
                    else:
                        from auth.student_auth import register_student
                        success, msg = register_student(name, email, roll, password)
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)


def show_teacher_dashboard():
    st.sidebar.title(f"Welcome, {st.session_state.user_data['name']}")
    st.sidebar.caption(f"Subject: {st.session_state.user_data['subject']}")
    if st.sidebar.button("Logout"):
        logout()
        st.rerun()

    page = st.sidebar.radio(
        "Navigation",
        ["My Exams", "Create Exam", "Generate Paper", "Evaluate Students", "Results"],
    )

    if page == "My Exams":
        show_teacher_exams()
    elif page == "Create Exam":
        show_create_exam()
    elif page == "Generate Paper":
        show_generate_paper()
    elif page == "Evaluate Students":
        show_evaluate_students()
    elif page == "Results":
        show_teacher_results()


def show_student_dashboard():
    st.sidebar.title(f"Welcome, {st.session_state.user_data['name']}")
    st.sidebar.caption(f"Roll: {st.session_state.user_data['roll_number']}")
    if st.sidebar.button("Logout"):
        logout()
        st.rerun()

    page = st.sidebar.radio("Navigation", ["Available Exams", "Take Exam", "Offline Exam", "My Results"])

    if page == "Available Exams":
        show_available_exams()
    elif page == "Take Exam":
        show_take_exam()
    elif page == "Offline Exam":
        show_offline_exam()
    elif page == "My Results":
        show_student_results()


# ===================== TEACHER PAGES =====================


def show_teacher_exams():
    st.title("My Exams")
    from database.db import get_exams_by_teacher
    exams = get_exams_by_teacher(st.session_state.user_data["id"])

    if not exams:
        st.info("No exams created yet. Go to 'Create Exam' to get started.")
        return

    for exam in exams:
        with st.expander(f"📋 {exam['title']} (ID: {exam['id']})"):
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Marks", exam["total_marks"])
            col2.metric("Questions", exam["num_mcq"] + exam["num_fill_blanks"] + exam["num_subjective"])
            col3.metric("Strictness", exam["evaluation_strictness"].capitalize())

            st.write(f"**MCQ:** {exam['num_mcq']} x {exam['marks_per_mcq']} marks")
            st.write(f"**Fill-in-the-Blanks:** {exam['num_fill_blanks']} x {exam['marks_per_fill']} marks")
            st.write(f"**Subjective:** {exam['num_subjective']} x {exam['marks_per_subjective']} marks")
            st.write(f"**Created:** {exam['created_at']}")


def show_create_exam():
    st.title("Create New Exam")

    title = st.text_input("Exam Title", placeholder="e.g., Mid-term Data Structures")

    st.subheader("Upload Course Material")
    pdf_files = st.file_uploader(
        "Upload PDF(s)", type=["pdf"], accept_multiple_files=True,
        help="Upload textbooks, notes, or any course material."
    )

    st.subheader("Marks Configuration")
    total_marks = st.number_input("Total Marks", min_value=10, max_value=500, value=100, step=5)

    col1, col2, col3 = st.columns(3)
    with col1:
        num_mcq = st.number_input("Number of MCQs", min_value=0, max_value=100, value=10)
        marks_mcq = st.number_input("Marks per MCQ", min_value=0.5, max_value=10.0, value=1.0, step=0.5)
    with col2:
        num_fill = st.number_input("Number of Fill-in-Blanks", min_value=0, max_value=50, value=5)
        marks_fill = st.number_input("Marks per Fill-in-Blank", min_value=0.5, max_value=10.0, value=2.0, step=0.5)
    with col3:
        num_sub = st.number_input("Number of Subjective", min_value=0, max_value=20, value=5)
        marks_sub = st.number_input("Marks per Subjective", min_value=1.0, max_value=20.0, value=10.0, step=0.5)

    calculated = (num_mcq * marks_mcq) + (num_fill * marks_fill) + (num_sub * marks_sub)
    st.info(f"Calculated total: {calculated} marks (Target: {total_marks})")

    st.subheader("Topic Weightage")
    st.caption("Add topics and their percentage weightage. If total is less than 100%, the remaining percentage will be covered by general/mixed topics from your material.")
    num_topics = st.number_input("Number of Topics", min_value=1, max_value=50, value=2)

    topics = {}
    for i in range(int(num_topics)):
        tc1, tc2 = st.columns([2, 1])
        topic_name = tc1.text_input(f"Topic {i+1} Name", key=f"topic_name_{i}")
        topic_weight = tc2.number_input(
            f"Weight %", min_value=1, max_value=100, value=max(1, 100 // int(num_topics)),
            key=f"topic_weight_{i}"
        )
        if topic_name:
            topics[topic_name] = topic_weight

    topic_total = sum(topics.values()) if topics else 0
    if topics and topic_total < 100:
        st.info(f"Topic weightages sum to {topic_total}%. The remaining {100 - topic_total}% will be assigned to **General** (mixed topics from your material).")
    elif topics and topic_total == 100:
        st.success("Topic weightages sum to 100%.")

    st.markdown("---")
    submitted = st.button("Create Exam & Process PDFs", type="primary")

    if submitted:
        # Validations
        if not title:
            st.error("Exam title is required.")
        elif not pdf_files:
            st.error("Please upload at least one PDF.")
        elif abs(calculated - total_marks) > 0.01:
            st.error(f"Marks don't add up. Calculated: {calculated}, Target: {total_marks}")
        elif not topics:
            st.error("At least one topic is required.")
        elif sum(topics.values()) > 100:
            st.error(f"Topic weightages exceed 100%. Current: {sum(topics.values())}%")
        else:
            # Fill remaining weightage with General topic
            remaining = 100 - sum(topics.values())
            if remaining > 0.01:
                topics["General"] = remaining
            import json
            import uuid

            with st.spinner("Processing PDFs and building knowledge base..."):
                # Extract text from PDFs
                from pdf_processing.extractor import extract_text_from_multiple_pdfs
                from pdf_processing.chunker import chunk_documents
                from rag.vector_store import add_documents
                from database.db import create_exam

                documents = extract_text_from_multiple_pdfs(pdf_files)
                st.write(f"Extracted text from {len(documents)} PDF(s)")

                # Chunk and embed
                chunks = chunk_documents(documents)
                st.write(f"Created {len(chunks)} chunks")

                # Store in ChromaDB
                collection_name = f"exam_{uuid.uuid4().hex[:12]}"
                add_documents(collection_name, chunks)
                st.write("Knowledge base created!")

                # Save exam to DB
                exam_id = create_exam(
                    teacher_id=st.session_state.user_data["id"],
                    title=title,
                    total_marks=total_marks,
                    num_mcq=num_mcq,
                    num_fill_blanks=num_fill,
                    num_subjective=num_sub,
                    marks_per_mcq=marks_mcq,
                    marks_per_fill=marks_fill,
                    marks_per_subjective=marks_sub,
                    topic_weightage=json.dumps(topics),
                    collection_name=collection_name,
                )

                st.success(f"Exam created successfully! Exam ID: {exam_id}")
                st.info("Now go to 'Generate Paper' to generate the question paper.")


def show_generate_paper():
    st.title("Generate Question Paper")

    from database.db import get_exams_by_teacher, get_questions_by_exam
    exams = get_exams_by_teacher(st.session_state.user_data["id"])

    if not exams:
        st.warning("No exams found. Create an exam first.")
        return

    exam_options = {f"{e['title']} (ID: {e['id']})": e for e in exams}
    selected = st.selectbox("Select Exam", list(exam_options.keys()))
    exam = exam_options[selected]

    # Check if questions already exist
    existing = get_questions_by_exam(exam["id"])
    if existing:
        st.warning(f"This exam already has {len(existing)} questions generated.")
        col_view, col_dl = st.columns(2)
        with col_view:
            if st.button("View Existing Questions"):
                display_question_paper(existing)
        with col_dl:
            from database.db import get_exam as _get_exam
            from utils.pdf_generator import generate_question_paper_pdf
            full_exam = _get_exam(exam["id"])
            pdf_bytes = generate_question_paper_pdf(
                full_exam, existing,
                teacher_name=full_exam["teacher_name"],
                teacher_subject=full_exam["teacher_subject"],
            )
            safe_title = exam["title"].replace(" ", "_")
            st.download_button(
                label="Download as PDF",
                data=pdf_bytes,
                file_name=f"{safe_title}_question_paper.pdf",
                mime="application/pdf",
                key="teacher_dl_existing",
            )
        st.markdown("---")

    if st.button("Generate New Question Paper", type="primary"):
        import json
        with st.spinner("Generating questions using AI... This may take a minute."):
            from generation.paper_builder import build_question_paper
            topics = json.loads(exam["topic_weightage"])

            questions = build_question_paper(
                exam_id=exam["id"],
                collection_name=exam["collection_name"],
                topics_weightage=topics,
                num_mcq=exam["num_mcq"],
                num_fill=exam["num_fill_blanks"],
                num_subjective=exam["num_subjective"],
                marks_per_mcq=exam["marks_per_mcq"],
                marks_per_fill=exam["marks_per_fill"],
                marks_per_subjective=exam["marks_per_subjective"],
            )

            st.success(f"Generated {len(questions)} questions!")
            display_question_paper(questions)


def display_question_paper(questions):
    """Display a formatted question paper."""
    mcqs = [q for q in questions if q.get("question_type") == "mcq"]
    fills = [q for q in questions if q.get("question_type") == "fill_blank"]
    subs = [q for q in questions if q.get("question_type") == "subjective"]

    if mcqs:
        st.subheader("Section A: Multiple Choice Questions")
        for i, q in enumerate(mcqs, 1):
            st.markdown(f"**Q{q.get('question_number', i)}.** {q['question_text']} [{q['marks']} marks]")
            import json
            options = q.get("options", "[]")
            if isinstance(options, str):
                options = json.loads(options)
            for opt in options:
                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;{opt}")
            st.markdown("")

    if fills:
        st.subheader("Section B: Fill in the Blanks")
        for i, q in enumerate(fills, 1):
            st.markdown(f"**Q{q.get('question_number', i)}.** {q['question_text']} [{q['marks']} marks]")

    if subs:
        st.subheader("Section C: Subjective Questions")
        for i, q in enumerate(subs, 1):
            st.markdown(f"**Q{q.get('question_number', i)}.** {q['question_text']} [{q['marks']} marks]")


def show_evaluate_students():
    st.title("Evaluate Student Submissions")

    from database.db import get_exams_by_teacher, get_submissions_by_exam, update_exam_strictness
    exams = get_exams_by_teacher(st.session_state.user_data["id"])

    if not exams:
        st.warning("No exams found.")
        return

    exam_options = {f"{e['title']} (ID: {e['id']})": e for e in exams}
    selected = st.selectbox("Select Exam", list(exam_options.keys()), key="eval_exam")
    exam = exam_options[selected]

    # Strictness selector
    strictness = st.select_slider(
        "Evaluation Strictness",
        options=["easy", "medium", "hard"],
        value=exam["evaluation_strictness"],
    )
    if strictness != exam["evaluation_strictness"]:
        update_exam_strictness(exam["id"], strictness)
        st.success(f"Strictness updated to: {strictness}")

    # Show submissions
    submissions = get_submissions_by_exam(exam["id"])
    if not submissions:
        st.info("No student submissions yet.")
        return

    st.subheader(f"Submissions ({len(submissions)})")
    for sub in submissions:
        mode_badge = "🌐 Online" if sub.get("attempt_mode", "online") == "online" else "📄 Offline"
        with st.expander(f"📄 {sub['student_name']} (Roll: {sub['roll_number']}) — {sub['status']} — {mode_badge}"):
            if sub["status"] == "evaluated":
                st.metric("Score", f"{sub['total_score']}/{sub['max_score']} ({sub['percentage']}%)")
            elif sub["status"] == "submitted":
                if st.button(f"Evaluate Now", key=f"eval_{sub['id']}"):
                    with st.spinner("Evaluating answers..."):
                        from database.db import get_answers_by_submission
                        from evaluation.scoring import evaluate_submission

                        # Get the pre-saved answers
                        answers = get_answers_by_submission(sub["id"])
                        if answers:
                            # Already has answer records, re-evaluate
                            student_answers = {a["question_id"]: a["student_answer"] for a in answers}
                        else:
                            st.error("No answers found for this submission.")
                            continue

                        result = evaluate_submission(sub["id"], exam["id"], student_answers)
                        st.success(f"Evaluation complete! Score: {result['total_score']}/{result['max_score']}")
                        st.rerun()


def show_teacher_results():
    st.title("Results Overview")

    from database.db import get_exams_by_teacher, get_submissions_by_exam
    exams = get_exams_by_teacher(st.session_state.user_data["id"])

    if not exams:
        st.warning("No exams found.")
        return

    exam_options = {f"{e['title']} (ID: {e['id']})": e for e in exams}
    selected = st.selectbox("Select Exam", list(exam_options.keys()), key="results_exam")
    exam = exam_options[selected]

    submissions = get_submissions_by_exam(exam["id"])
    evaluated = [s for s in submissions if s["status"] == "evaluated"]

    if not evaluated:
        st.info("No evaluated submissions yet.")
        return

    # Summary metrics
    scores = [s["percentage"] for s in evaluated]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Students Evaluated", len(evaluated))
    col2.metric("Average Score", f"{sum(scores)/len(scores):.1f}%")
    col3.metric("Highest", f"{max(scores):.1f}%")
    col4.metric("Lowest", f"{min(scores):.1f}%")

    # Individual results
    st.subheader("Individual Results")
    for sub in evaluated:
        mode_badge = "🌐" if sub.get("attempt_mode", "online") == "online" else "📄"
        with st.expander(f"{mode_badge} {sub['student_name']} — {sub['total_score']}/{sub['max_score']} ({sub['percentage']}%)"):
            from evaluation.feedback import generate_submission_report
            report = generate_submission_report(sub["id"])

            if "section_scores" in report:
                for section, scores_data in report["section_scores"].items():
                    if scores_data["total"] > 0:
                        st.write(f"**{section}:** {scores_data['scored']}/{scores_data['total']}")

            if "answers" in report:
                for a in report["answers"]:
                    status = "✅" if a["marks_awarded"] == a["max_marks"] else "⚠️" if a["marks_awarded"] > 0 else "❌"
                    st.markdown(f"{status} **{a['question_text'][:80]}...** — {a['marks_awarded']}/{a['max_marks']}")
                    if a["feedback"]:
                        st.caption(f"Feedback: {a['feedback']}")


# ===================== STUDENT PAGES =====================


def show_available_exams():
    st.title("Available Exams")

    from database.db import get_all_exams, get_questions_by_exam
    exams = get_all_exams()

    if not exams:
        st.info("No exams available currently.")
        return

    for exam in exams:
        questions = get_questions_by_exam(exam["id"])
        if not questions:
            continue  # Only show exams with generated questions

        with st.expander(f"📋 {exam['title']} — {exam['total_marks']} marks"):
            st.write(f"**Set by:** {exam['teacher_name']} ({exam['teacher_subject']})")
            st.write(f"**MCQs:** {exam['num_mcq']}")
            st.write(f"**Fill-in-the-Blanks:** {exam['num_fill_blanks']}")
            st.write(f"**Subjective:** {exam['num_subjective']}")
            st.write(f"**Total marks:** {exam['total_marks']}")
            st.info(f"Exam ID: **{exam['id']}** — Use this in 'Take Exam' page.")


def show_take_exam():
    st.title("Take Exam")

    exam_id = st.number_input("Enter Exam ID", min_value=1, step=1)

    from database.db import get_exam, get_questions_by_exam, get_submission_by_student_exam
    exam = get_exam(exam_id)

    if not exam:
        st.warning("Enter a valid Exam ID from 'Available Exams'.")
        return

    # Duplicate submission check
    existing_sub = get_submission_by_student_exam(st.session_state.user_data["id"], exam_id)
    if existing_sub:
        st.error(f"You have already submitted this exam (Status: {existing_sub['status']}). "
                 "Multiple submissions are not allowed.")
        return

    questions = get_questions_by_exam(exam_id)
    if not questions:
        st.warning("This exam has no questions generated yet.")
        return

    st.subheader(f"📝 {exam['title']} — Total: {exam['total_marks']} marks")
    st.info(f"**Question paper set by:** {exam['teacher_name']} — {exam['teacher_subject']}")
    st.markdown("---")

    import json
    student_answers = {}

    with st.form("answer_form"):
        # MCQs
        mcqs = [q for q in questions if q["question_type"] == "mcq"]
        if mcqs:
            st.subheader("Section A: Multiple Choice Questions")
            for q in mcqs:
                st.markdown(f"**Q{q['question_number']}.** {q['question_text']} [{q['marks']} marks]")
                options = json.loads(q["options"]) if isinstance(q["options"], str) else q["options"]
                answer = st.radio(
                    "Select answer:", options,
                    key=f"mcq_{q['id']}", index=None,
                )
                if answer:
                    student_answers[q["id"]] = answer[0]  # First character (A, B, C, D)
                st.markdown("")

        # Fill in the blanks
        fills = [q for q in questions if q["question_type"] == "fill_blank"]
        if fills:
            st.subheader("Section B: Fill in the Blanks")
            for q in fills:
                st.markdown(f"**Q{q['question_number']}.** {q['question_text']} [{q['marks']} marks]")
                answer = st.text_input("Your answer:", key=f"fill_{q['id']}")
                student_answers[q["id"]] = answer

        # Subjective
        subs = [q for q in questions if q["question_type"] == "subjective"]
        if subs:
            st.subheader("Section C: Subjective Questions")
            for q in subs:
                st.markdown(f"**Q{q['question_number']}.** {q['question_text']} [{q['marks']} marks]")
                answer = st.text_area("Your answer:", key=f"sub_{q['id']}", height=150)
                student_answers[q["id"]] = answer

        submitted = st.form_submit_button("Submit Answers", type="primary")

        if submitted:
            if not any(v.strip() for v in student_answers.values() if isinstance(v, str)):
                st.error("Please answer at least one question.")
            else:
                from database.db import create_submission
                from evaluation.scoring import evaluate_submission

                with st.spinner("Submitting and evaluating your answers..."):
                    sub_id = create_submission(exam_id, st.session_state.user_data["id"], attempt_mode="online")

                    result = evaluate_submission(sub_id, exam_id, student_answers)

                    st.success(
                        f"Submitted! Score: {result['total_score']}/{result['max_score']} "
                        f"({result['percentage']}%)"
                    )
                    st.balloons()


def show_offline_exam():
    st.title("Offline Exam")

    tab_download, tab_upload = st.tabs(["Download Question Paper", "Upload Answer Sheet"])

    # ---- Download Tab ----
    with tab_download:
        st.subheader("Download Question Paper as PDF")

        from database.db import get_all_exams, get_questions_by_exam, get_exam

        all_exams = get_all_exams()
        # Filter to exams that have generated questions
        exams_with_questions = []
        for e in all_exams:
            qs = get_questions_by_exam(e["id"])
            if qs:
                exams_with_questions.append(e)

        if not exams_with_questions:
            st.info("No exams with generated questions are available.")
        else:
            exam_options = {f"{e['title']} (ID: {e['id']})": e for e in exams_with_questions}
            selected = st.selectbox("Select Exam", list(exam_options.keys()), key="offline_dl_exam")
            exam = exam_options[selected]

            questions = get_questions_by_exam(exam["id"])
            st.write(f"**{exam['title']}** — {exam['total_marks']} marks — {len(questions)} questions")

            from utils.pdf_generator import generate_question_paper_pdf

            pdf_bytes = generate_question_paper_pdf(
                exam, questions,
                teacher_name=exam["teacher_name"],
                teacher_subject=exam["teacher_subject"],
            )

            safe_title = exam["title"].replace(" ", "_")
            st.download_button(
                label="Download Question Paper PDF",
                data=pdf_bytes,
                file_name=f"{safe_title}_question_paper.pdf",
                mime="application/pdf",
            )

            # In-app preview of the question paper
            with st.expander("Preview Question Paper"):
                display_question_paper(questions)

    # ---- Upload Tab ----
    with tab_upload:
        st.subheader("Upload Your Answer Sheet")

        exam_id = st.number_input("Enter Exam ID", min_value=1, step=1, key="offline_upload_exam_id")

        from database.db import get_exam, get_questions_by_exam, get_submission_by_student_exam

        exam = get_exam(exam_id)
        if not exam:
            st.warning("Enter a valid Exam ID.")
        else:
            # Duplicate submission check
            existing_sub = get_submission_by_student_exam(st.session_state.user_data["id"], exam_id)
            if existing_sub:
                st.error(f"You have already submitted this exam (Status: {existing_sub['status']}). "
                         "Multiple submissions are not allowed.")
            else:
                questions = get_questions_by_exam(exam_id)
                if not questions:
                    st.warning("This exam has no questions generated yet.")
                else:
                    st.write(f"**{exam['title']}** — {exam['total_marks']} marks — {len(questions)} questions")

                    uploaded_file = st.file_uploader(
                        "Upload your answer sheet (PDF)",
                        type=["pdf"],
                        key="offline_answer_pdf",
                    )

                    if uploaded_file is not None:
                        # File size validation
                        from config.settings import MAX_PDF_SIZE_MB
                        file_size_mb = uploaded_file.size / (1024 * 1024)
                        if file_size_mb > MAX_PDF_SIZE_MB:
                            st.error(f"File too large ({file_size_mb:.1f} MB). Maximum allowed: {MAX_PDF_SIZE_MB} MB.")
                        else:
                            # Use session state to cache extraction results across reruns
                            cache_key = f"offline_parsed_{exam_id}_{uploaded_file.name}_{uploaded_file.size}"

                            if st.session_state.get("_offline_cache_key") != cache_key:
                                # New file uploaded — run extraction + parsing
                                try:
                                    from utils.answer_parser import extract_text_from_answer_sheet, parse_answers_from_text

                                    with st.spinner("Extracting text from your answer sheet..."):
                                        raw_text = extract_text_from_answer_sheet(uploaded_file)

                                    if not raw_text or len(raw_text.strip()) < 5:
                                        st.error("Could not extract any text from the uploaded PDF. "
                                                 "Please ensure it contains readable text or clear handwriting.")
                                        st.stop()

                                    with st.spinner("Parsing your answers using AI..."):
                                        parsed_answers = parse_answers_from_text(raw_text, questions)

                                    # Cache results in session state
                                    st.session_state["_offline_cache_key"] = cache_key
                                    st.session_state["_offline_raw_text"] = raw_text
                                    st.session_state["_offline_parsed"] = parsed_answers

                                except Exception as e:
                                    st.error(f"Failed to process your answer sheet: {e}")
                                    st.info("Please try uploading again. If the issue persists, ensure your PDF "
                                            "contains clear, readable text.")
                                    st.stop()

                            # Retrieve cached results
                            raw_text = st.session_state.get("_offline_raw_text", "")
                            parsed_answers = st.session_state.get("_offline_parsed", {})

                            with st.expander("Extracted text (click to view)"):
                                st.text(raw_text[:3000])

                            # Editable parsed answers
                            st.subheader("Parsed Answers — Review & Edit")
                            st.caption("You can correct any answers that were parsed incorrectly before submitting.")

                            q_lookup = {q["id"]: q for q in questions}
                            edited_answers = {}

                            for q in questions:
                                q_id = q["id"]
                                default_val = parsed_answers.get(q_id, "")
                                label = f"Q{q['question_number']} ({q['question_type']}) [{q['marks']} marks]: {q['question_text'][:100]}"

                                if q["question_type"] == "subjective":
                                    edited_answers[q_id] = st.text_area(
                                        label, value=default_val,
                                        key=f"edit_ans_{q_id}", height=100,
                                    )
                                else:
                                    edited_answers[q_id] = st.text_input(
                                        label, value=default_val,
                                        key=f"edit_ans_{q_id}",
                                    )

                            answered_count = sum(1 for a in edited_answers.values() if a.strip())
                            st.info(f"Answers provided for {answered_count} out of {len(questions)} questions.")

                            # Confirm and submit
                            if st.button("Confirm & Submit", type="primary", key="offline_submit"):
                                from database.db import create_submission
                                from evaluation.scoring import evaluate_submission

                                try:
                                    with st.spinner("Submitting and evaluating your answers..."):
                                        sub_id = create_submission(
                                            exam_id, st.session_state.user_data["id"],
                                            attempt_mode="offline",
                                        )
                                        result = evaluate_submission(sub_id, exam_id, edited_answers)

                                    # Clear cache after successful submission
                                    st.session_state.pop("_offline_cache_key", None)
                                    st.session_state.pop("_offline_raw_text", None)
                                    st.session_state.pop("_offline_parsed", None)

                                    st.success(
                                        f"Submitted! Score: {result['total_score']}/{result['max_score']} "
                                        f"({result['percentage']}%)"
                                    )
                                    st.balloons()
                                except Exception as e:
                                    st.error(f"Submission failed: {e}")


def show_student_results():
    st.title("My Results")

    from database.db import get_submissions_by_student
    submissions = get_submissions_by_student(st.session_state.user_data["id"])

    if not submissions:
        st.info("No submissions yet. Take an exam to see results here.")
        return

    for sub in submissions:
        status_icon = {"pending": "⏳", "submitted": "📤", "evaluated": "✅"}.get(sub["status"], "")
        with st.expander(f"{status_icon} {sub['exam_title']} — {sub['status'].capitalize()}"):
            if sub["status"] == "evaluated":
                col1, col2, col3 = st.columns(3)
                col1.metric("Score", f"{sub['total_score']}/{sub['max_score']}")
                col2.metric("Percentage", f"{sub['percentage']}%")

                grade = "A+" if sub["percentage"] >= 90 else "A" if sub["percentage"] >= 80 else \
                    "B" if sub["percentage"] >= 70 else "C" if sub["percentage"] >= 60 else \
                    "D" if sub["percentage"] >= 50 else "F"
                col3.metric("Grade", grade)

                # Detailed breakdown
                from evaluation.feedback import generate_submission_report
                report = generate_submission_report(sub["id"])

                if "section_scores" in report:
                    st.subheader("Section-wise Breakdown")
                    for section, scores_data in report["section_scores"].items():
                        if scores_data["total"] > 0:
                            pct = (scores_data["scored"] / scores_data["total"]) * 100
                            st.progress(pct / 100, text=f"{section}: {scores_data['scored']}/{scores_data['total']} ({pct:.0f}%)")

                if "answers" in report:
                    st.subheader("Question-wise Feedback")
                    for a in report["answers"]:
                        status = "✅" if a["marks_awarded"] == a["max_marks"] else "⚠️" if a["marks_awarded"] > 0 else "❌"
                        st.markdown(f"{status} **Q:** {a['question_text'][:100]}")
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;**Your answer:** {a['student_answer'][:200]}")
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;**Marks:** {a['marks_awarded']}/{a['max_marks']}")
                        if a["feedback"]:
                            st.caption(f"💬 {a['feedback']}")
                        st.markdown("---")
            else:
                st.write(f"Submitted at: {sub['submitted_at']}")
                st.write("Awaiting evaluation...")


# ===================== MAIN =====================

if st.session_state.logged_in:
    if st.session_state.user_type == "teacher":
        show_teacher_dashboard()
    else:
        show_student_dashboard()
else:
    show_login_page()
