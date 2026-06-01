from backend.app.services.llm_service import _build_extractive_fallback_answer


def test_fallback_answer_prefers_direct_response_over_source_labels():
    answer = _build_extractive_fallback_answer(
        "Who is Jai and what are his key skills?",
        [
            {
                "content": (
                    "Website Summary\n"
                    "Entity name: Jai Prakash.\n"
                    "Primary roles: Data Scientist, Machine Learning Engineer, AI Engineer.\n"
                    "Key skills: Python, machine learning, generative AI, automation.\n"
                    "Profile highlights: Jai Prakash builds AI assistants and automation systems."
                )
            }
        ],
    )

    assert "Based on the uploaded content" not in answer
    assert "Source URL" not in answer
    assert "Page title" not in answer
    assert "Data Scientist" in answer or "Jai Prakash" in answer


def test_fallback_answer_formats_skills_questions_more_naturally():
    answer = _build_extractive_fallback_answer(
        "What are his key skills?",
        [
            {
                "content": (
                    "Website Summary\n"
                    "Entity name: Jai Prakash.\n"
                    "Primary roles: Data Scientist, Machine Learning Engineer, AI Engineer.\n"
                    "Key skills: Python, machine learning, generative AI, automation."
                )
            }
        ],
    )

    assert "Key skills include" in answer
    assert "Based on the uploaded content" not in answer
