from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv

from excel_output import build_excel
from research_agent import ResearchError, research_school
from school_input import parse_csv_schools, parse_pasted_schools


load_dotenv()

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

st.set_page_config(
    page_title="Faculty Research Tool",
    page_icon="🔎",
    layout="wide",
)

st.title("Faculty Research Tool")
st.caption(
    "Upload or paste a school list, run the configured research workflow, "
    "and download one Excel workbook."
)

with st.form("research_form"):
    left, right = st.columns(2)

    with left:
        discipline = st.text_input("Discipline or academic area", value="Accounting")
        included_rank = st.text_input("Rank to include", value="Associate Professor")
        current_only = st.checkbox("Current faculty only", value=True)
        official_only = st.checkbox(
            "Official university/school sources only",
            value=True,
            disabled=True,
        )

    with right:
        exclusions = st.multiselect(
            "Excluded appointment types",
            DEFAULT_EXCLUSIONS,
            default=DEFAULT_EXCLUSIONS,
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
        help="A School Name column is enough. An optional Official Roster URL column can override automatic selection.",
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
        st.error(
            "OPENAI_API_KEY is missing. Add it to the .env file before running."
        )
        st.stop()

    records = []
    if uploaded is not None:
        records.extend(parse_csv_schools(uploaded))
    records.extend(parse_pasted_schools(pasted))

    # Preserve order while removing duplicate school names.
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

    st.info(f"Processing {len(records)} school(s). Official roster pages will be selected automatically.")
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
                included_rank=included_rank,
                exclusions=exclusions,
                current_only=current_only,
                official_only=official_only,
                model=model,
                roster_url=record["roster_url"],
            )
            results.append(result)
        except ResearchError as exc:
            failures.append((school, str(exc)))
        except Exception as exc:  # Keep the UI alive on unexpected API/network errors.
            failures.append((school, f"Unexpected error: {exc}"))

        progress.progress(index / len(records))

    status.write("Research run finished.")

    if results:
        configuration = {
            "Discipline": discipline,
            "Included rank": included_rank,
            "Current faculty only": current_only,
            "Official sources only": official_only,
            "Exclusions": exclusions,
            "Model": model,
            "Schools submitted": len(records),
            "Schools completed": len(results),
            "Schools failed": len(failures),
        }
        workbook_bytes = build_excel(
            results=results,
            configuration=configuration,
        )

        included = sum(
            1
            for result in results
            for person in result["faculty_classifications"]
            if person["decision"] == "included"
        )
        needs_review = sum(
            1
            for result in results
            for person in result["faculty_classifications"]
            if person["decision"] == "needs_review"
        )

        completed_results = [
            result for result in results
            if result["school_status"] == "completed"
        ]
        incomplete_results = [
            result for result in results
            if result["school_status"] == "incomplete"
        ]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Candidates", included)
        col2.metric("Needs review", needs_review)
        col3.metric("Schools completed", len(completed_results))
        col4.metric("Schools incomplete", len(incomplete_results))

        for result in incomplete_results:
            st.warning(
                f"{result['school_name']} was incomplete: "
                f"{result['school_note']}"
            )

        st.download_button(
            "Download Excel report",
            data=workbook_bytes,
            file_name="faculty_research_results.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            type="primary",
            use_container_width=True,
        )

    if failures:
        st.warning("Some schools failed:")
        for school, message in failures:
            st.write(f"- **{school}:** {message}")
