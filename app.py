from __future__ import annotations

import os
import inspect
import re

import streamlit as st
from dotenv import load_dotenv

from excel_output import build_excel
from research_agent import ResearchError, research_school
from school_input import parse_csv_schools, parse_pasted_schools
from version import APP_VERSION


load_dotenv()

# Fail fast if files from different releases were mixed together.
_required_params = {"discipline_variants", "allow_personal_websites"}
_actual_params = set(inspect.signature(research_school).parameters)
_missing_params = _required_params - _actual_params
if _missing_params:
    raise RuntimeError(
        "Mixed application versions detected. research_agent.py is older than app.py. "
        "Replace the entire project folder from the same release. Missing parameters: "
        + ", ".join(sorted(_missing_params))
    )

DEFAULT_EXCLUSIONS = [
    "Practice / Professor of Practice",
    "Non-tenure-track",
    "Teaching / Teaching Track",
    "Instructional",
    "Adjunct",
    "Clinical / Clinic",
    "Emeritus / Emerita",
    "Visiting",
    "Research Associate Professor",
    "Educator Track",
]


def parse_variants(value: str) -> list[str]:
    parts = re.split(r"[,;\n]+", value)
    seen = set()
    output = []
    for part in parts:
        cleaned = " ".join(part.strip().split())
        if cleaned and cleaned.casefold() not in seen:
            seen.add(cleaned.casefold())
            output.append(cleaned)
    return output


st.set_page_config(
    page_title="Peer Scholars Search Tool",
    page_icon="🔎",
    layout="wide",
)

st.title("Peer Scholars Search Tool")
st.caption(f"Version {APP_VERSION}")
st.caption(
    "Define the peer-scholar search, upload or paste a school list, and download "
    "one standardized Excel workbook."
)

with st.form("research_form"):
    left, right = st.columns(2)

    with left:
        discipline = st.text_input("Discipline or academic area", value="Accounting")
        variants_text = st.text_input(
            "Variants of name",
            value="Accountancy",
            help=(
                "Comma-separated equivalent area names. Examples: Accountancy; "
                "Decision and Operations. Only the names you enter here are treated "
                "as equivalent to the primary discipline."
            ),
        )
        included_rank = st.text_input("Rank to include", value="Associate Professor")
        current_only = st.checkbox("Current faculty only", value=True)
        official_only = st.checkbox(
            "Official sources control current eligibility",
            value=True,
            disabled=True,
            help=(
                "Current roster membership, discipline, rank, and appointment type "
                "must come from official school/university sources."
            ),
        )

    with right:
        exclusions = st.multiselect(
            "Excluded appointment types",
            DEFAULT_EXCLUSIONS,
            default=DEFAULT_EXCLUSIONS,
        )
        allow_personal_websites = st.checkbox(
            "Search personal academic websites for missing details",
            value=True,
            help=(
                "Personal academic sites may fill Ph.D. year, first year of rank, "
                "or CV link. They cannot add a candidate or override current "
                "official rank/affiliation. Wikipedia and LinkedIn remain excluded."
            ),
        )
        model = st.text_input(
            "OpenAI model",
            value=os.getenv("OPENAI_MODEL", "gpt-5.6"),
            help="Keep the default unless you intentionally want another supported model.",
        )
        max_schools = st.number_input(
            "Maximum schools for this run",
            min_value=1,
            max_value=100,
            value=3,
            help="Start with 1-3 schools while validating the workflow.",
        )

    uploaded = st.file_uploader(
        "Upload school list as CSV",
        type=["csv"],
        help=(
            "A School Name column is enough. An optional Official Roster URL column "
            "can override automatic selection."
        ),
    )
    pasted = st.text_area(
        "Or paste one school per line",
        height=150,
        placeholder="Duke University (Fuqua)\nUniversity of Florida (Warrington)",
    )

    submitted = st.form_submit_button(
        "Run Research",
        type="primary",
        use_container_width=True,
    )

if submitted:
    if not os.getenv("OPENAI_API_KEY"):
        st.error("OPENAI_API_KEY is missing. Add it to the .env file before running.")
        st.stop()

    discipline_variants = parse_variants(variants_text)
    records = []
    if uploaded is not None:
        records.extend(parse_csv_schools(uploaded))
    records.extend(parse_pasted_schools(pasted))

    unique_records = []
    seen = set()
    for record in records:
        key = record["school_name"].casefold()
        if key not in seen:
            seen.add(key)
            unique_records.append(record)
    records = unique_records[: int(max_schools)]

    if not records:
        st.error("Upload a CSV or paste at least one school.")
        st.stop()

    st.info(
        f"Processing {len(records)} school(s). Current eligibility uses official "
        "sources; supplemental personal-site research is "
        f"{'enabled' if allow_personal_websites else 'disabled'}."
    )
    progress = st.progress(0)
    status = st.empty()
    results = []
    failures = []

    for index, record in enumerate(records, start=1):
        school = record["school_name"]
        status.write(f"Researching **{school}** ({index}/{len(records)})")
        try:
            result = research_school(
                school=school,
                discipline=discipline,
                discipline_variants=discipline_variants,
                included_rank=included_rank,
                exclusions=exclusions,
                current_only=current_only,
                official_only=official_only,
                allow_personal_websites=allow_personal_websites,
                model=model,
                roster_url=record["roster_url"],
            )
            results.append(result)
        except ResearchError as exc:
            failures.append((school, str(exc)))
        except Exception as exc:
            failures.append((school, f"Unexpected error: {exc}"))
        progress.progress(index / len(records))

    status.write("Research run finished.")

    if results:
        configuration = {
            "Discipline": discipline,
            "Variants of name": discipline_variants,
            "Included rank": included_rank,
            "Current faculty only": current_only,
            "Official sources control eligibility": official_only,
            "Personal academic website enrichment": allow_personal_websites,
            "Exclusions": exclusions,
            "Model": model,
            "Schools submitted": len(records),
            "Schools returned": len(results),
            "Schools failed": len(failures),
        }
        workbook_bytes = build_excel(results=results, configuration=configuration)

        included = sum(
            1 for result in results for person in result["faculty_classifications"]
            if person["decision"] == "included"
        )
        needs_review = sum(
            1 for result in results for person in result["faculty_classifications"]
            if person["decision"] == "needs_review"
        )
        completed_results = [r for r in results if r["school_status"] == "completed"]
        incomplete_results = [r for r in results if r["school_status"] == "incomplete"]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Candidates", included)
        col2.metric("Needs review", needs_review)
        col3.metric("Schools completed", len(completed_results))
        col4.metric("Schools incomplete", len(incomplete_results))

        for result in incomplete_results:
            st.warning(f"{result['school_name']} was incomplete: {result['school_note']}")

        st.download_button(
            "Download Excel report",
            data=workbook_bytes,
            file_name="peer_scholars_search_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True,
        )

    if failures:
        st.warning("Some schools failed:")
        for school, message in failures:
            st.write(f"- **{school}:** {message}")
