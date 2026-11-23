from app.models import GovernmentScheme


def demo_schemes() -> list[GovernmentScheme]:
    return [
        GovernmentScheme(
            id=key,
            title=title,
            category=category,
            summary=summary,
            eligibility=["Fictional example for local development", eligibility],
            documents=["Demo proof of residence", "Demo supporting record (do not upload)"],
            guidance=[
                "Review the example eligibility criteria.",
                "Create a local assistance case to explore the workflow.",
                "No application is submitted to any government department.",
            ],
        )
        for key, title, category, summary, eligibility in [
            (
                "demo-harvest",
                "Harvest Support",
                "Agriculture",
                "An example of seasonal support for small farming households.",
                "Example: a small farming household",
            ),
            (
                "demo-learning",
                "Learning Pathways",
                "Education",
                "An example of assistance with learning materials for rural students.",
                "Example: a student in a rural school",
            ),
            (
                "demo-senior",
                "Senior Care Companion",
                "Wellbeing",
                "An example of community support for older residents.",
                "Example: a resident aged 60 or above",
            ),
        ]
    ]
