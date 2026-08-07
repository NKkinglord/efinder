from excel_output import build_excel
from school_input import parse_pasted_schools
from school_registry import (
    RANKED_SCHOOL_COUNT,
    REGISTRY_SCHOOL_COUNT,
    resolve_known_school,
)
from utils import discipline_labels, safe_search_domains


def main():
    schools = parse_pasted_schools(
        "Duke University (Fuqua)\nDuke University (Fuqua)\nRice University"
    )
    assert schools == [
        {"school_name": "Duke University (Fuqua)", "roster_url": ""},
        {"school_name": "Rice University", "roster_url": ""},
    ]

    assert RANKED_SCHOOL_COUNT == 101
    assert REGISTRY_SCHOOL_COUNT == 103

    duke = resolve_known_school("Duke")
    assert duke is not None
    assert duke.canonical_name == "Duke University (Fuqua)"
    assert duke.roster_url == "https://www.fuqua.duke.edu/faculty-research/directory/all"
    for value in [
        "Duke University (Fuqua)",
        "Duke University (Fuqua School of Business)",
        "Duke University Fuqua School of Business",
        "Fuqua School of Business",
        "random wording duke accounting faculty",
        "peer list - FUQUA - current faculty",
    ]:
        assert resolve_known_school(value) == duke, value

    expected_aliases = {
        "USC": "University of Southern California (Marshall)",
        "UT": "University of Texas at Austin (McCombs)",
        "UT Dallas Jindal": "University of Texas at Dallas (Jindal)",
        "UW": "University of Washington (Foster)",
        "Harvard HBS": "Harvard Business School",
        "LBS": "London Business School",
        "Cambridge Judge": "University of Cambridge (Judge Business School)",
        "Oxford Said": "University of Oxford (Saïd Business School)",
        "NUS": "National University of Singapore (NUS Business School)",
        "NTU Singapore Nanyang": "Nanyang Technological University (Nanyang Business School)",
        "HKUST": "Hong Kong University of Science and Technology (HKUST Business School)",
        "IIM Bangalore": "Indian Institute of Management Bangalore",
        "Melbourne Business School": "Melbourne Business School",
        "RSM": "Erasmus University Rotterdam (Rotterdam School of Management)",
        "CEIBS": "China Europe International Business School (CEIBS)",
        "UCT GSB": "University of Cape Town Graduate School of Business",
        "Qatar University": "Qatar University (College of Business and Economics)",
        "York Schulich": "York University (Schulich)",
        "UQ Business School": "University of Queensland Business School",
        "Michigan State Broad": "Michigan State University (Broad)",
        "Michigan Ross": "University of Michigan (Ross)",
        "Georgia Tech Scheller": "Georgia Institute of Technology (Scheller)",
        "UGA Terry": "University of Georgia (Terry)",
    }
    for text_value, canonical in expected_aliases.items():
        resolved = resolve_known_school(text_value)
        assert resolved is not None, text_value
        assert resolved.canonical_name == canonical, (text_value, resolved.canonical_name)

    assert resolve_known_school("Dukes County Business School") is None
    assert resolve_known_school("Unknown Example School") is None

    labels = discipline_labels("Accounting", ["Accountancy", " accounting ", ""])
    assert labels == ["Accounting", "Accountancy"]

    # International public-suffix safety.
    assert "ac.uk" not in safe_search_domains("https://www.jbs.cam.ac.uk/faculty/")
    assert "edu.sg" not in safe_search_domains("https://mba.nus.edu.sg/faculty/")
    assert "edu.hk" not in safe_search_domains("https://business.hku.hk/faculty/")
    assert "ac.in" not in safe_search_domains("https://www.iimb.ac.in/faculty")
    assert safe_search_domains(
        "https://www.jbs.cam.ac.uk/faculty/", ("cam.ac.uk",)
    )[0] == "cam.ac.uk"

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
