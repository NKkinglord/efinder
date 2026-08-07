from __future__ import annotations

import csv
import io
from typing import BinaryIO


def _clean(value: object) -> str:
    return " ".join(str(value or "").strip().split())


def parse_pasted_schools(text: str) -> list[dict[str, str]]:
    records = []
    for line in text.splitlines():
        cleaned = line.strip()
        if not cleaned:
            continue

        if "|" in cleaned:
            school, roster_url = cleaned.split("|", 1)
        else:
            school, roster_url = cleaned, ""

        school = _clean(school)
        roster_url = roster_url.strip()
        if school:
            records.append(
                {"school_name": school, "roster_url": roster_url}
            )
    return deduplicate(records)


def parse_csv_schools(uploaded_file: BinaryIO) -> list[dict[str, str]]:
    raw = uploaded_file.getvalue()
    text = raw.decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        return []

    normalized_header = [_clean(cell).casefold() for cell in rows[0]]
    school_headers = {
        "school",
        "school name",
        "business school",
        "university",
        "university name",
    }
    roster_headers = {
        "official roster url",
        "roster url",
        "faculty roster url",
        "official faculty url",
    }

    has_header = any(value in school_headers for value in normalized_header)
    school_col = next(
        (i for i, value in enumerate(normalized_header) if value in school_headers),
        0,
    )
    roster_col = next(
        (i for i, value in enumerate(normalized_header) if value in roster_headers),
        None,
    )

    data_rows = rows[1:] if has_header else rows
    records = []
    for row in data_rows:
        if school_col >= len(row):
            continue
        school = _clean(row[school_col])
        roster_url = ""
        if roster_col is not None and roster_col < len(row):
            roster_url = row[roster_col].strip()
        if school:
            records.append(
                {"school_name": school, "roster_url": roster_url}
            )

    return deduplicate(records)


def deduplicate(records: list[dict[str, str]]) -> list[dict[str, str]]:
    seen = set()
    output = []
    for record in records:
        key = record["school_name"].casefold()
        if key not in seen:
            seen.add(key)
            output.append(record)
    return output
