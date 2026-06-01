from backend.app.services.website_ingestion import build_website_summary


def test_build_website_summary_extracts_roles_skills_and_services():
    pages = [
        {
            "url": "https://portfolio.example.com",
            "title": "Jai Prakash | Data Scientist | Machine Learning Engineer",
            "content": (
                "Overview: Jai Prakash is a Data Scientist and Machine Learning Engineer. "
                "He helps startups build AI assistants, workflow automation, and retrieval systems. "
                "His skills include Python, machine learning, generative AI, and automation."
            ),
        },
        {
            "url": "https://portfolio.example.com/projects",
            "title": "Projects",
            "content": (
                "Projects: He developed a SaaS platform and an AI copilot product. "
                "Contact him at jai@example.com for consulting."
            ),
        },
    ]

    summary = build_website_summary(pages)

    assert "Entity name: Jai Prakash" in summary
    assert "Primary roles:" in summary
    assert "Data Scientist" in summary
    assert "Machine Learning Engineer" in summary
    assert "Key skills:" in summary
    assert "Python" in summary
    assert "Machine Learning" in summary
    assert "Services and offerings:" in summary
    assert "Products or platforms:" in summary
    assert "Contact signals:" in summary
