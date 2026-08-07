from __future__ import annotations

import io
from typing import Any

import xlsxwriter


CANDIDATE_HEADERS = [
    "Candidate Name",
    "School Name",
    "Discipline",
    "Rank",
    "Year of Ph.D.",
    "First Year of the Rank",
    "Link to CV",
]

REVIEW_HEADERS = [
    "Candidate Name",
    "School Name",
    "Possible Discipline",
    "Possible Rank",
    "Year of Ph.D.",
    "First Year of the Rank",
    "Link to CV",
    "Review Reason",
    "Official Evidence Links",
]

AUDIT_HEADERS = [
    "Candidate Name",
    "School Name",
    "Eligibility Decision",
    "Current Rank",
    "Current Official Source",
    "Year of Ph.D.",
    "First Year Used",
    "First-Year Basis",
    "Confidence",
    "Notes",
    "Evidence URLs",
]

SUMMARY_HEADERS = [
    "School Name",
    "Qualifying Candidates",
    "Needs Review",
    "Roster Source",
    "Status",
    "Notes",
]


def build_excel(
    *,
    results: list[dict[str, Any]],
    configuration: dict[str, Any],
) -> bytes:
    buffer = io.BytesIO()
    workbook = xlsxwriter.Workbook(buffer, {"in_memory": True})

    header = workbook.add_format(
        {
            "bold": True,
            "font_color": "white",
            "bg_color": "#1F4E78",
            "border": 1,
            "align": "center",
            "valign": "vcenter",
        }
    )
    body = workbook.add_format({"border": 1, "valign": "top"})
    wrap = workbook.add_format({"border": 1, "valign": "top", "text_wrap": True})
    year_format = workbook.add_format(
        {"border": 1, "valign": "top", "num_format": "0"}
    )
    url_format = workbook.add_format(
        {"font_color": "blue", "underline": 1, "border": 1, "valign": "top"}
    )

    candidates = workbook.add_worksheet("Candidates")
    reviews = workbook.add_worksheet("Needs Review")
    summary = workbook.add_worksheet("School Summary")
    audit = workbook.add_worksheet("Source Audit")
    config = workbook.add_worksheet("Run Configuration")

    _write_headers(candidates, CANDIDATE_HEADERS, header)
    _write_headers(reviews, REVIEW_HEADERS, header)
    _write_headers(summary, SUMMARY_HEADERS, header)
    _write_headers(audit, AUDIT_HEADERS, header)

    candidate_row = 1
    review_row = 1
    audit_row = 1
    summary_row = 1

    for result in results:
        included_count = 0
        review_count = 0

        for person in result["faculty_classifications"]:
            evidence_text = " | ".join(person["evidence_urls"])
            decision = person["decision"]

            if decision == "included":
                included_count += 1
                values = [
                    person["candidate_name"],
                    result["school_name"],
                    person["discipline"],
                    person["current_rank"],
                    person["phd_year"],
                    person["first_year_of_rank"],
                    person["profile_or_cv_url"],
                ]
                _write_candidate_row(
                    candidates,
                    candidate_row,
                    values,
                    body,
                    year_format,
                    url_format,
                )
                candidate_row += 1

            elif decision == "needs_review":
                review_count += 1
                values = [
                    person["candidate_name"],
                    result["school_name"],
                    person["discipline"],
                    person["current_rank"],
                    person["phd_year"],
                    person["first_year_of_rank"],
                    person["profile_or_cv_url"],
                    person["exclusion_or_review_reason"],
                    evidence_text,
                ]
                _write_review_row(
                    reviews,
                    review_row,
                    values,
                    body,
                    wrap,
                    year_format,
                    url_format,
                )
                review_row += 1

            audit_values = [
                person["candidate_name"],
                result["school_name"],
                decision,
                person["current_rank"],
                person["current_source"],
                person["phd_year"],
                person["first_year_of_rank"],
                person["first_year_basis"],
                person["confidence"],
                person["notes"],
                evidence_text,
            ]
            _write_audit_row(
                audit,
                audit_row,
                audit_values,
                body,
                wrap,
                year_format,
                url_format,
            )
            audit_row += 1

        summary_values = [
            result["school_name"],
            included_count,
            review_count,
            result["roster_source"],
            result["school_status"],
            result["school_note"],
        ]
        _write_summary_row(
            summary,
            summary_row,
            summary_values,
            body,
            wrap,
            url_format,
        )
        summary_row += 1

    _write_configuration(config, configuration, header, body)

    for sheet in [candidates, reviews, summary, audit]:
        sheet.freeze_panes(1, 0)
        sheet.autofilter(0, 0, max(sheet.dim_rowmax, 1), sheet.dim_colmax)

    candidates.set_column("A:A", 24)
    candidates.set_column("B:B", 42)
    candidates.set_column("C:D", 28)
    candidates.set_column("E:F", 20)
    candidates.set_column("G:G", 55)

    reviews.set_column("A:A", 24)
    reviews.set_column("B:B", 42)
    reviews.set_column("C:D", 28)
    reviews.set_column("E:F", 20)
    reviews.set_column("G:G", 50)
    reviews.set_column("H:I", 55)

    summary.set_column("A:A", 42)
    summary.set_column("B:C", 20)
    summary.set_column("D:D", 55)
    summary.set_column("E:E", 16)
    summary.set_column("F:F", 55)

    audit.set_column("A:A", 24)
    audit.set_column("B:B", 42)
    audit.set_column("C:D", 28)
    audit.set_column("E:E", 55)
    audit.set_column("F:G", 18)
    audit.set_column("H:I", 25)
    audit.set_column("J:K", 60)

    config.set_column("A:A", 28)
    config.set_column("B:B", 80)

    workbook.close()
    buffer.seek(0)
    return buffer.read()


def _write_headers(sheet, headers, fmt):
    for col, value in enumerate(headers):
        sheet.write(0, col, value, fmt)


def _write_candidate_row(sheet, row, values, body, year_fmt, url_fmt):
    for col, value in enumerate(values):
        if col in {4, 5} and value is not None:
            sheet.write_number(row, col, value, year_fmt)
        elif col == 6 and value:
            sheet.write_url(row, col, value, url_fmt, string=value)
        else:
            sheet.write(row, col, "" if value is None else value, body)


def _write_review_row(sheet, row, values, body, wrap, year_fmt, url_fmt):
    for col, value in enumerate(values):
        if col in {4, 5} and value is not None:
            sheet.write_number(row, col, value, year_fmt)
        elif col == 6 and value:
            sheet.write_url(row, col, value, url_fmt, string=value)
        elif col in {7, 8}:
            sheet.write(row, col, "" if value is None else value, wrap)
        else:
            sheet.write(row, col, "" if value is None else value, body)


def _write_audit_row(sheet, row, values, body, wrap, year_fmt, url_fmt):
    for col, value in enumerate(values):
        if col in {5, 6} and value is not None:
            sheet.write_number(row, col, value, year_fmt)
        elif col == 4 and value:
            sheet.write_url(row, col, value, url_fmt, string=value)
        elif col in {9, 10}:
            sheet.write(row, col, "" if value is None else value, wrap)
        else:
            sheet.write(row, col, "" if value is None else value, body)


def _write_summary_row(sheet, row, values, body, wrap, url_fmt):
    for col, value in enumerate(values):
        if col in {1, 2}:
            sheet.write_number(row, col, value, body)
        elif col == 3 and value:
            sheet.write_url(row, col, value, url_fmt, string=value)
        elif col == 5:
            sheet.write(row, col, value, wrap)
        else:
            sheet.write(row, col, value, body)


def _write_configuration(sheet, configuration, header, body):
    sheet.write(0, 0, "Setting", header)
    sheet.write(0, 1, "Value", header)
    for row, (key, value) in enumerate(configuration.items(), start=1):
        sheet.write(row, 0, key, body)
        if isinstance(value, list):
            value = ", ".join(value)
        sheet.write(row, 1, str(value), body)
