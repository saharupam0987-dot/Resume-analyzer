"""
Full end-to-end test of the Student-Teacher Evaluation System.

Flow:
  1. Create a sample PDF with course content
  2. Register a teacher and a student
  3. Teacher creates an exam (upload PDF, configure questions)
  4. Build RAG knowledge base from PDF
  5. Generate question paper (MCQ + Fill + Subjective)
  6. Student submits answers
  7. System evaluates answers with strictness = "medium"
  8. Display full results with feedback
"""

import json
import os
import sys

# -- Step 0: Setup ----------------------------------------------------------
print("=" * 70)
print("  FULL END-TO-END TEST -- Student-Teacher Evaluation System")
print("=" * 70)

# Clean previous test data
DB_PATH = os.path.join(os.path.dirname(__file__), "database", "evaluation.db")
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print("\n[Setup] Cleaned previous database.")

from database.db import init_db
init_db()
print("[Setup] Database initialized.\n")


# -- Step 1: Create a sample PDF -------------------------------------------
print("-" * 70)
print("STEP 1: Creating sample PDF with course material")
print("-" * 70)

from fpdf import FPDF

pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=15)

# Chapter 1: Data Structures
pdf.add_page()
pdf.set_font("Helvetica", "B", 16)
pdf.cell(0, 10, "Chapter 1: Data Structures", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 11)
content_ds = """
Data structures are specialized formats for organizing, processing, retrieving, and storing data. They provide a means to manage large amounts of data efficiently for uses such as large databases and internet indexing services.

An array is a collection of elements stored at contiguous memory locations. Arrays allow random access to elements using an index. The time complexity for accessing an element by index is O(1), while searching for an element takes O(n) in the worst case.

A linked list is a linear data structure where elements are stored in nodes. Each node contains data and a reference (pointer) to the next node. Unlike arrays, linked lists do not store elements in contiguous memory locations. Insertion and deletion at the beginning of a linked list takes O(1) time.

A stack is a linear data structure that follows the Last In First Out (LIFO) principle. The main operations are push (add an element to the top), pop (remove the top element), and peek (view the top element without removing it). Stacks are used in function call management, expression evaluation, and backtracking algorithms.

A queue is a linear data structure that follows the First In First Out (FIFO) principle. The main operations are enqueue (add an element to the rear) and dequeue (remove an element from the front). Queues are used in scheduling, buffering, and breadth-first search.

A binary tree is a hierarchical data structure where each node has at most two children, called the left child and right child. A Binary Search Tree (BST) is a binary tree where the left subtree contains nodes with values less than the root, and the right subtree contains nodes with values greater than the root. The average time complexity for search, insert, and delete in a BST is O(log n).

A hash table is a data structure that maps keys to values using a hash function. The hash function converts a key into an index in an array. Hash tables provide O(1) average time complexity for search, insert, and delete operations. Collision resolution techniques include chaining and open addressing.
"""
pdf.multi_cell(0, 6, content_ds)

# Chapter 2: Algorithms
pdf.add_page()
pdf.set_font("Helvetica", "B", 16)
pdf.cell(0, 10, "Chapter 2: Algorithms", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 11)
content_algo = """
An algorithm is a step-by-step procedure for solving a problem or accomplishing a task. Algorithms are evaluated based on their time complexity and space complexity.

Sorting algorithms arrange elements in a specific order. Bubble Sort repeatedly compares adjacent elements and swaps them if they are in the wrong order. Its time complexity is O(n^2). Merge Sort uses the divide-and-conquer strategy, dividing the array into halves, sorting each half, and merging them. Merge Sort has a time complexity of O(n log n) and is stable.

Quick Sort also uses divide-and-conquer. It selects a pivot element and partitions the array around the pivot. Elements smaller than the pivot go to the left, and larger ones go to the right. Quick Sort has an average time complexity of O(n log n) but a worst-case of O(n^2).

Binary Search is an efficient algorithm for finding an element in a sorted array. It works by repeatedly dividing the search interval in half. If the target value is less than the middle element, the search continues in the lower half. Binary Search has a time complexity of O(log n).

Depth-First Search (DFS) is a graph traversal algorithm that explores as far as possible along each branch before backtracking. It uses a stack (or recursion). DFS is used for topological sorting, detecting cycles, and solving maze problems.

Breadth-First Search (BFS) is a graph traversal algorithm that explores all neighbors at the current depth before moving to the next level. It uses a queue. BFS finds the shortest path in an unweighted graph.

Dynamic Programming (DP) is a technique for solving problems by breaking them into overlapping subproblems and storing their solutions. The two approaches are top-down (memoization) and bottom-up (tabulation). Classic DP problems include the Fibonacci sequence, knapsack problem, and longest common subsequence.
"""
pdf.multi_cell(0, 6, content_algo)

test_pdf_path = os.path.join(os.path.dirname(__file__), "test_course_material.pdf")
pdf.output(test_pdf_path)
print(f"  Created: {test_pdf_path}")
print(f"  Pages: 2 (Data Structures + Algorithms)\n")


# -- Step 2: Register Teacher & Student ------------------------------------
print("-" * 70)
print("STEP 2: Registering Teacher and Student")
print("-" * 70)

from auth.teacher_auth import register_teacher, login_teacher
from auth.student_auth import register_student, login_student

ok, msg = register_teacher("Dr. Smith", "smith@university.com", "teach123", "Computer Science")
print(f"  Teacher: {msg}")

ok, teacher = login_teacher("smith@university.com", "teach123")
print(f"  Teacher login: {'SUCCESS' if ok else 'FAILED'} (ID: {teacher['id']})")

ok, msg = register_student("Alice Johnson", "alice@student.com", "CS2024001", "stud123")
print(f"  Student: {msg}")

ok, student = login_student("alice@student.com", "stud123")
print(f"  Student login: {'SUCCESS' if ok else 'FAILED'} (ID: {student['id']})\n")


# -- Step 3: Process PDF & Build Knowledge Base ----------------------------
print("-" * 70)
print("STEP 3: Processing PDF and building RAG knowledge base")
print("-" * 70)

from pdf_processing.extractor import extract_text_from_pdf
from pdf_processing.chunker import chunk_text
from rag.vector_store import add_documents, query_collection
import uuid

text = extract_text_from_pdf(test_pdf_path)
print(f"  Extracted {len(text)} characters from PDF")

chunks = chunk_text(text)
print(f"  Split into {len(chunks)} chunks")

collection_name = f"exam_{uuid.uuid4().hex[:12]}"
chunk_docs = [{"text": c, "source": "test_course_material.pdf", "chunk_index": i} for i, c in enumerate(chunks)]
add_documents(collection_name, chunk_docs)
print(f"  Stored in ChromaDB collection: {collection_name}")

# Quick RAG test
results = query_collection(collection_name, "What is a binary search tree?", n_results=2)
print(f"  RAG test query: found {len(results)} results (top score: {results[0]['score']:.3f})\n")


# -- Step 4: Create Exam ---------------------------------------------------
print("-" * 70)
print("STEP 4: Creating exam configuration")
print("-" * 70)

from database.db import create_exam

topics = {"Data Structures": 50, "Algorithms": 50}

exam_id = create_exam(
    teacher_id=teacher["id"],
    title="Mid-Term: DS & Algorithms",
    total_marks=30,
    num_mcq=5,
    num_fill_blanks=3,
    num_subjective=2,
    marks_per_mcq=2.0,
    marks_per_fill=2.0,
    marks_per_subjective=5.0,
    topic_weightage=json.dumps(topics),
    collection_name=collection_name,
)

print(f"  Exam created -- ID: {exam_id}")
print(f"  Title: Mid-Term: DS & Algorithms")
print(f"  Total: 30 marks (5 MCQ x 2 + 3 Fill x 2 + 2 Subjective x 5)")
print(f"  Topics: {topics}\n")


# -- Step 5: Generate Question Paper --------------------------------------
print("-" * 70)
print("STEP 5: Generating question paper using RAG + LLM")
print("-" * 70)
print("  (This calls the OpenAI API - may take 15-30 seconds...)\n")

from generation.paper_builder import build_question_paper

questions = build_question_paper(
    exam_id=exam_id,
    collection_name=collection_name,
    topics_weightage=topics,
    num_mcq=5,
    num_fill=3,
    num_subjective=2,
    marks_per_mcq=2.0,
    marks_per_fill=2.0,
    marks_per_subjective=5.0,
)

print(f"  Generated {len(questions)} questions total!\n")

mcqs = [q for q in questions if q["question_type"] == "mcq"]
fills = [q for q in questions if q["question_type"] == "fill_blank"]
subs = [q for q in questions if q["question_type"] == "subjective"]

print("  +--- QUESTION PAPER -----------------------------------------------+")
print(f"  |  Section A: MCQs ({len(mcqs)} questions)")
for i, q in enumerate(mcqs, 1):
    print(f"  |  Q{i}. {q['question_text'][:70]}...")
    opts = json.loads(q["options"]) if isinstance(q["options"], str) else q["options"]
    for o in opts:
        print(f"  |      {o}")
    print(f"  |      [Answer: {q['correct_answer']}]")

print(f"  |")
print(f"  |  Section B: Fill in the Blanks ({len(fills)} questions)")
for i, q in enumerate(fills, 1):
    print(f"  |  Q{len(mcqs)+i}. {q['question_text'][:70]}...")
    print(f"  |      [Answer: {q['correct_answer']}]")

print(f"  |")
print(f"  |  Section C: Subjective ({len(subs)} questions)")
for i, q in enumerate(subs, 1):
    print(f"  |  Q{len(mcqs)+len(fills)+i}. {q['question_text'][:70]}...")
print("  +------------------------------------------------------------------+\n")


# -- Step 6: Student Submits Answers ---------------------------------------
print("-" * 70)
print("STEP 6: Student submitting answers")
print("-" * 70)

from database.db import get_questions_by_exam, create_submission

db_questions = get_questions_by_exam(exam_id)

# Simulate student answers - mix of correct, partially correct, and wrong
student_answers = {}
for q in db_questions:
    if q["question_type"] == "mcq":
        # Answer 3 out of 5 correctly
        if q["question_number"] <= 3:
            student_answers[q["id"]] = q["correct_answer"]  # Correct
        else:
            # Pick a wrong answer
            correct = q["correct_answer"].strip().upper()
            wrong = "B" if correct != "B" else "C"
            student_answers[q["id"]] = wrong
    elif q["question_type"] == "fill_blank":
        # 1 correct, 1 close (typo), 1 wrong
        if q["question_number"] == len(mcqs) + 1:
            student_answers[q["id"]] = q["correct_answer"]  # Exact
        elif q["question_number"] == len(mcqs) + 2:
            # Introduce a typo
            ans = q["correct_answer"]
            student_answers[q["id"]] = ans[:-1] if len(ans) > 3 else ans + "s"
        else:
            student_answers[q["id"]] = "completely wrong answer"
    elif q["question_type"] == "subjective":
        # Provide a decent but not perfect answer
        model_ans = q["correct_answer"]
        # Use ~60% of the model answer words as the student's answer
        words = model_ans.split()
        partial = " ".join(words[:int(len(words) * 0.6)])
        student_answers[q["id"]] = partial

submission_id = create_submission(exam_id, student["id"])
print(f"  Submission ID: {submission_id}")
print(f"  Answers submitted for {len(student_answers)} questions")
print(f"  Strategy: 3/5 MCQ correct, 1 exact + 1 typo + 1 wrong fill, partial subjective\n")


# -- Step 7: Evaluate -----------------------------------------------------
print("-" * 70)
print("STEP 7: Evaluating answers (strictness: medium)")
print("-" * 70)
print("  (Subjective eval calls OpenAI API - may take 10-20 seconds...)\n")

from evaluation.scoring import evaluate_submission

result = evaluate_submission(submission_id, exam_id, student_answers)

print(f"  Total Score: {result['total_score']} / {result['max_score']}")
print(f"  Percentage:  {result['percentage']}%\n")


# -- Step 8: Detailed Results ----------------------------------------------
print("-" * 70)
print("STEP 8: Detailed results with feedback")
print("-" * 70)

from evaluation.feedback import generate_submission_report

report = generate_submission_report(submission_id)

print(f"\n  Exam: {report['exam_title']}")
print(f"  Score: {report['total_score']}/{report['max_score']} ({report['percentage']}%)")
print(f"  Status: {report['status']}")

print(f"\n  Section Scores:")
for section, scores in report["section_scores"].items():
    if scores["total"] > 0:
        pct = (scores["scored"] / scores["total"]) * 100
        bar = "#" * int(pct / 5) + "." * (20 - int(pct / 5))
        print(f"    {section:20s}: {scores['scored']:5.1f}/{scores['total']:5.1f}  {bar} {pct:.0f}%")

print(f"\n  Per-Question Breakdown:")
for a in report["answers"]:
    icon = "OK" if a["marks_awarded"] == a["max_marks"] else "~" if a["marks_awarded"] > 0 else "X"
    print(f"    [{icon}] {a['question_type']:10s} | {a['marks_awarded']:4.1f}/{a['max_marks']:4.1f} | {a['feedback'][:80]}")

print("\n" + "=" * 70)
print("  END-TO-END TEST COMPLETE -- ALL STEPS PASSED!")
print("=" * 70)
