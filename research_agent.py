from __future__ import annotations

import json
import os
import re
from typing import Any
from urllib.parse import urlparse

from openai import OpenAI

from protocol import ROSTER_SYSTEM_PROTOCOL, VERIFICATION_SYSTEM_PROTOCOL
from schemas import ROSTER_DISCOVERY_SCHEMA, SCHOOL_RESULT_SCHEMA
from school_registry import resolve_known_school


class ResearchError(RuntimeError):
    pass


def _normalized_name(value: str) -> str:
    value = re.sub(r"[^\w\s]", " ", value.casefold())
    return " ".join(value.split())


def _parse_json_response(response: Any, *, stage: str) -> dict[str, Any]:
    if response.status == "incomplete":
        reason = getattr(response.incomplete_details, "reason", "unknown")
        raise ResearchError(f"{stage} response incomplete: {reason}")

    if not response.output_text:
        raise ResearchError(f"{stage} returned no output text.")

    try:
        return json.loads(response.output_text)
    except json.JSONDecodeError as exc:
        raise ResearchError(f"{stage} did not return valid JSON.") from exc


def _domain_filters(roster_url: str) -> list[str]:
    hostname = (urlparse(roster_url).hostname or "").lower()
    if not hostname:
        return []

    domains = [hostname]
    labels = hostname.split(".")
    if len(labels) >= 2:
        root = ".".join(labels[-2:])
        if root not in domains:
            domains.append(root)
    return domains


def discover_current_roster(
    *,
    client: OpenAI,
    model: str,
    school: str,
    discipline: str,
    roster_url: str = "",
) -> dict[str, Any]:
    exact_url_instruction = (
        f"Use this exact official roster URL: {roster_url}"
        if roster_url
        else "Locate the exact current official discipline faculty roster URL."
    )

    request = f"""
School: {school}
Discipline/area: {discipline}

{exact_url_instruction}

Extract only names visibly presented as current faculty on this one official
source. A full-school directory is acceptable only when it visibly labels each
selected person with the requested discipline/academic area. Do not use Ph.D.
pages, research pages, publication pages, award pages, news pages, archived
pages, or independently discovered profiles to add names.

If the source does not expose both names and discipline labels to the web tool,
return incomplete.
"""

    response = client.responses.create(
        model=model,
        reasoning={"effort": "high"},
        tools=[
            {
                "type": "web_search",
                "filters": {
                    "blocked_domains": [
                        "wikipedia.org",
                        "linkedin.com",
                        "signalhire.com",
                        "researchgate.net",
                    ]
                },
            }
        ],
        tool_choice="required",
        include=["web_search_call.action.sources"],
        input=[
            {"role": "system", "content": ROSTER_SYSTEM_PROTOCOL},
            {"role": "user", "content": request},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "current_faculty_roster",
                "strict": True,
                "schema": ROSTER_DISCOVERY_SCHEMA,
            }
        },
        max_output_tokens=8000,
    )

    roster = _parse_json_response(response, stage="Roster discovery")
    _validate_roster(roster, requested_school=school)

    if roster_url and roster["roster_source"].rstrip("/") != roster_url.rstrip("/"):
        raise ResearchError(
            f"{school}: roster discovery did not use the supplied roster URL."
        )

    return roster


def verify_roster(
    *,
    client: OpenAI,
    model: str,
    school: str,
    discipline: str,
    included_rank: str,
    exclusions: list[str],
    roster: dict[str, Any],
) -> dict[str, Any]:
    roster_members = roster["roster_members"]
    closed_roster = [
        {
            "name": member["name"],
            "displayed_title": member["displayed_title"],
            "profile_url": member["profile_url"],
        }
        for member in roster_members
    ]

    request = f"""
School: {school}
Discipline/area: {discipline}
Included rank: {included_rank}
Excluded appointment types/titles: {", ".join(exclusions) if exclusions else "None"}
Exact current roster source: {roster["roster_source"]}

CLOSED CURRENT ROSTER:
{json.dumps(closed_roster, ensure_ascii=False, indent=2)}

Classify every supplied name exactly once. Do not add any other name.
Use official sources only.
"""

    allowed_domains = _domain_filters(roster["roster_source"])
    web_tool: dict[str, Any] = {
        "type": "web_search",
        "filters": {
            "blocked_domains": [
                "wikipedia.org",
                "linkedin.com",
                "signalhire.com",
                "researchgate.net",
            ]
        },
    }
    if allowed_domains:
        web_tool["filters"]["allowed_domains"] = allowed_domains

    response = client.responses.create(
        model=model,
        reasoning={"effort": "high"},
        tools=[web_tool],
        tool_choice="required",
        include=["web_search_call.action.sources"],
        input=[
            {"role": "system", "content": VERIFICATION_SYSTEM_PROTOCOL},
            {"role": "user", "content": request},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "verified_faculty_classifications",
                "strict": True,
                "schema": SCHOOL_RESULT_SCHEMA,
            }
        },
        max_output_tokens=18000,
    )

    result = _parse_json_response(response, stage="Candidate verification")
    result["roster_source"] = roster["roster_source"]
    _validate_school_result(
        result,
        requested_school=school,
        roster_members=roster_members,
    )
    return result


def research_school(
    *,
    school: str,
    discipline: str,
    included_rank: str,
    exclusions: list[str],
    current_only: bool = True,
    official_only: bool = True,
    model: str | None = None,
    roster_url: str = "",
) -> dict[str, Any]:
    if not os.getenv("OPENAI_API_KEY"):
        raise ResearchError("OPENAI_API_KEY is not configured.")

    if not current_only:
        raise ResearchError("Version 0.2 currently supports current faculty only.")
    if not official_only:
        raise ResearchError("Version 0.2 requires official sources only.")

    client = OpenAI()
    selected_model = model or os.getenv("OPENAI_MODEL", "gpt-5.6")

    configured = resolve_known_school(school) if not roster_url else None
    preferred_roster_url = roster_url or (configured.roster_url if configured else "")
    resolution_method = (
        "user-supplied roster URL"
        if roster_url
        else "built-in school registry"
        if configured
        else "automatic web discovery"
    )

    roster = discover_current_roster(
        client=client,
        model=selected_model,
        school=school,
        discipline=discipline,
        roster_url=preferred_roster_url,
    )

    # A saved registry URL may become stale or unreadable. In that case, try one
    # automatic discovery pass rather than forcing the user to find a replacement.
    if (
        roster["roster_status"] == "incomplete"
        and configured is not None
        and not roster_url
    ):
        roster = discover_current_roster(
            client=client,
            model=selected_model,
            school=school,
            discipline=discipline,
            roster_url="",
        )
        resolution_method = "automatic web discovery after registry fallback"

    if roster["roster_status"] == "incomplete":
        return {
            "school_name": school,
            "roster_source": roster["roster_source"],
            "school_status": "incomplete",
            "school_note": (
                "Strict roster discovery could not directly read the current "
                f"faculty names. No candidates were inferred. {roster['roster_note']} "
                f"Roster source method: {resolution_method}."
            ),
            "faculty_classifications": [],
        }

    result = verify_roster(
        client=client,
        model=selected_model,
        school=school,
        discipline=discipline,
        included_rank=included_rank,
        exclusions=exclusions,
        roster=roster,
    )
    prefix = f"Roster source selected by {resolution_method}."
    result["school_note"] = (
        f"{prefix} {result['school_note']}".strip()
    )
    return result


def _validate_roster(
    roster: dict[str, Any],
    *,
    requested_school: str,
) -> None:
    required = {
        "school_name",
        "discipline",
        "roster_source",
        "roster_status",
        "roster_note",
        "roster_members",
    }
    missing = required.difference(roster)
    if missing:
        raise ResearchError(f"Roster fields missing: {sorted(missing)}")

    if roster["roster_status"] == "completed":
        if not roster["roster_source"]:
            raise ResearchError(
                f"{requested_school}: completed roster has no source URL."
            )
        if not roster["roster_members"]:
            raise ResearchError(
                f"{requested_school}: completed roster contains no members."
            )

    names = [_normalized_name(m["name"]) for m in roster["roster_members"]]
    if len(names) != len(set(names)):
        raise ResearchError(f"{requested_school}: duplicate roster names found.")


def _validate_school_result(
    result: dict[str, Any],
    *,
    requested_school: str,
    roster_members: list[dict[str, str]],
) -> None:
    if not isinstance(result.get("faculty_classifications"), list):
        raise ResearchError("faculty_classifications must be a list.")

    roster_by_name = {
        _normalized_name(member["name"]): member
        for member in roster_members
    }
    output_names = [
        _normalized_name(person["candidate_name"])
        for person in result["faculty_classifications"]
    ]

    extras = sorted(set(output_names).difference(roster_by_name))
    missing = sorted(set(roster_by_name).difference(output_names))

    if extras:
        raise ResearchError(
            f"{requested_school}: model added names outside the current roster: "
            f"{extras}"
        )
    if missing:
        raise ResearchError(
            f"{requested_school}: model failed to classify roster members: "
            f"{missing}"
        )
    if len(output_names) != len(set(output_names)):
        raise ResearchError(
            f"{requested_school}: duplicate faculty classifications found."
        )

    for person in result["faculty_classifications"]:
        if person["decision"] == "included" and not person["current_source"]:
            raise ResearchError(
                f"{requested_school}: included candidate "
                f"{person['candidate_name']} has no current official source."
            )
