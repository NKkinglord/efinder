from excel_output import build_excel
from school_input import parse_pasted_schools
from school_registry import resolve_known_school
from utils import discipline_labels


def main():
    schools = parse_pasted_schools(
        "Duke University (Fuqua)\nDuke University (Fuqua)\nRice University"
    )
    assert schools == [
        {"school_name": "Duke University (Fuqua)", "roster_url": ""},
        {"school_name": "Rice University", "roster_url": ""},
    ]

    duke = resolve_known_school("Duke")
    assert duke is not None
    assert duke.canonical_name == "Duke University (Fuqua)"
    assert duke.roster_url == "https://www.fuqua.duke.edu/faculty-research/directory/all"
    assert resolve_known_school("Duke University (Fuqua)") == duke
    assert resolve_known_school("Unknown Example School") is None

    labels = discipline_labels("Accounting", ["Accountancy", " accounting ", ""])
    assert labels == ["Accounting", "Accountancy"]

    sample = {
        "school_name": "Duke University (Fuqua)",
        "roster_source": duke.roster_url,
        "school_status": "completed",
        "school_note": "Sample data only.",
        "faculty_classifications": [
            {
                "candidate_name": "Sample Person",
                "discipline": "Accounting",
                "current_rank": "Associate Professor",
                "decision": "included",
                "exclusion_or_review_reason": "",
                "phd_year": 2020,
                "first_year_of_rank": 2025,
                "first_year_basis": "exact_promotion_appointment",
                "profile_or_cv_url": "https://example.edu/sample",
                "current_source": "https://example.edu/sample",
                "evidence_urls": ["https://example.edu/sample"],
                "confidence": "high",
                "notes": "Sample data only.",
            }
        ],
    }
    output = build_excel(
        results=[sample],
        configuration={
            "Discipline": "Accounting",
            "Variants of name": ["Accountancy"],
            "Personal academic website enrichment": True,
        },
    )
    assert len(output) > 1000
    print("Smoke test passed.")


if __name__ == "__main__":
    main()
