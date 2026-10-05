import json
import math
from rag.retriever import retrieve_context_for_topics
from generation.question_generator import generate_mcqs, generate_fill_blanks, generate_subjective
from database.db import insert_questions


def distribute_questions(topics_weightage: dict, total_count: int) -> dict[str, int]:
    """Distribute questions across topics based on weightage.

    Args:
        topics_weightage: Dict of {topic: weight_percentage} e.g. {"ML": 40, "DL": 60}
        total_count: Total number of questions to distribute.

    Returns:
        Dict of {topic: question_count}
    """
    distribution = {}
    total_weight = sum(topics_weightage.values())
    remaining = total_count

    topics = list(topics_weightage.keys())
    for i, topic in enumerate(topics):
        weight = topics_weightage[topic] / total_weight
        if i == len(topics) - 1:
            # Last topic gets the remainder
            distribution[topic] = remaining
        else:
            count = max(1, round(total_count * weight))
            count = min(count, remaining)
            distribution[topic] = count
            remaining -= count

    return distribution


def build_question_paper(exam_id: int, collection_name: str,
                         topics_weightage: dict,
                         num_mcq: int, num_fill: int, num_subjective: int,
                         marks_per_mcq: float, marks_per_fill: float,
                         marks_per_subjective: float) -> list[dict]:
    """Build a complete question paper by generating questions per topic.

    Args:
        exam_id: The exam ID in the database.
        collection_name: ChromaDB collection for RAG.
        topics_weightage: {topic: percentage} dict.
        num_mcq: Total MCQs to generate.
        num_fill: Total fill-in-the-blanks.
        num_subjective: Total subjective questions.
        marks_per_mcq: Marks per MCQ.
        marks_per_fill: Marks per fill-in-the-blank.
        marks_per_subjective: Marks per subjective.

    Returns:
        List of all generated question dicts.
    """
    topics = list(topics_weightage.keys())

    # Retrieve context for all topics at once
    topic_contexts = retrieve_context_for_topics(collection_name, topics)

    all_questions = []
    question_number = 1

    # Distribute each question type across topics
    if num_mcq > 0:
        mcq_dist = distribute_questions(topics_weightage, num_mcq)
        for topic, count in mcq_dist.items():
            if count <= 0:
                continue
            context = topic_contexts.get(topic, "")
            if not context:
                continue
            questions = generate_mcqs(context, topic, count, marks_per_mcq)
            for q in questions:
                q["question_number"] = question_number
                question_number += 1
            all_questions.extend(questions)

    if num_fill > 0:
        fill_dist = distribute_questions(topics_weightage, num_fill)
        for topic, count in fill_dist.items():
            if count <= 0:
                continue
            context = topic_contexts.get(topic, "")
            if not context:
                continue
            questions = generate_fill_blanks(context, topic, count, marks_per_fill)
            for q in questions:
                q["question_number"] = question_number
                question_number += 1
            all_questions.extend(questions)

    if num_subjective > 0:
        sub_dist = distribute_questions(topics_weightage, num_subjective)
        for topic, count in sub_dist.items():
            if count <= 0:
                continue
            context = topic_contexts.get(topic, "")
            if not context:
                continue
            questions = generate_subjective(context, topic, count, marks_per_subjective)
            for q in questions:
                q["question_number"] = question_number
                question_number += 1
            all_questions.extend(questions)

    # Save to database
    insert_questions(exam_id, all_questions)

    return all_questions
