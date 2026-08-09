from __future__ import annotations

import json
import os
import re
from typing import Any

from openai import OpenAI

from protocol import (
    ROSTER_SYSTEM_PROTOCOL,
    SUPPLEMENTAL_SYSTEM_PROTOCOL,
    VERIFICATION_SYSTEM_PROTOCOL,
)
from schemas import (
    ROSTER_DISCOVERY_SCHEMA,
    SCHOOL_RESULT_SCHEMA,
    SUPPLEMENTAL_RESULT_SCHEMA,
)
from school_registry import resolve_known_school
from utils import discipline_labels, resolve_rank_search_rules, safe_search_domains


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


_domain_filters = safe_search_domains



def discover_current_roster(
    *,
    client: OpenAI,
    model: str,
    school: str,
    discipline: str,
    discipline_variants: list[str],
    roster_url: str = "",
    official_domains: tuple[str, ...] | list[str] = (),
) -> dict[str, Any]:
    exact_url_instruction = (
        f"Use this exact official roster URL: {roster_url}"
        if roster_url
        else "Locate the exact current official discipline faculty roster URL."
    )
    labels = discipline_labels(discipline, discipline_variants)
    request = f"""
School: {school}
Primary discipline/area: {discipline}
Accepted discipline keywords/phrases: {json.dumps(labels, ensure_ascii=False)}

{exact_url_instruction}

Treat each accepted item as a case-insensitive keyword or phrase. An official
discipline/area label qualifies when it contains the primary discipline or any
of the supplied variant terms. Extract only names visibly presented as current
faculty on this one official source under a qualifying label. A full-school
directory is acceptable only when it visibly labels each selected person with a
qualifying discipline/area label.

If the source does not expose both names and discipline labels to the web tool,
return incomplete.
"""
    response = client.responses.create(
        model=model,
        reasoning={"effort": "high"},
        tools=[{
            "type": "web_search",
            "filters": {
                **({"allowed_domains": _domain_filters(roster_url, official_domains)}
                   if _domain_filters(roster_url, official_domains) else {}),
                "blocked_domains": [
                    "wikipedia.org", "linkedin.com", "signalhire.com",
                    "researchgate.net",
                ],
            },
        }],
        tool_choice="required",
        include=["web_search_call.action.sources"],
        input=[
            {"role": "system", "content": ROSTER_SYSTEM_PROTOCOL},
            {"role": "user", "content": request},
        ],
        text={"format": {
            "type": "json_schema",
            "name": "current_faculty_roster",
            "strict": True,
            "schema": ROSTER_DISCOVERY_SCHEMA,
        }},
        max_output_tokens=8000,
    )
    roster = _parse_json_response(response, stage="Roster discovery")
    _validate_roster(roster, requested_school=school)
    if roster_url and roster["roster_source"].rstrip("/") != roster_url.rstrip("/"):
        raise ResearchError(f"{school}: roster discovery did not use the supplied roster URL.")
    return roster


def verify_roster(
    *,
    client: OpenAI,
    model: str,
    school: str,
    discipline: str,
    discipline_variants: list[str],
    included_rank: str,
    exclusions: list[str],
    roster: dict[str, Any],
    official_domains: tuple[str, ...] | list[str] = (),
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
    labels = discipline_labels(discipline, discipline_variants)
    canonical_ranks, automatic_rank_exclusions, effective_exclusions = resolve_rank_search_rules(
        included_rank, exclusions
    )
    if not canonical_ranks:
        raise ResearchError("At least one included rank is required.")
    request = f"""
School: {school}
Primary discipline/area: {discipline}
Accepted discipline keywords/phrases: {json.dumps(labels, ensure_ascii=False)}
Rank(s) entered by user: {included_rank}
Effective included ranks (OR logic): {json.dumps(canonical_ranks, ensure_ascii=False)}
Automatic rank exclusions: {", ".join(automatic_rank_exclusions) if automatic_rank_exclusions else "None"}
Effective excluded appointment types/titles: {", ".join(effective_exclusions) if effective_exclusions else "None"}
Exact current roster source: {roster["roster_source"]}

CLOSED CURRENT ROSTER:
{json.dumps(closed_roster, ensure_ascii=False, indent=2)}

Classify every supplied name exactly once. Do not add any other name.
Use official university/school sources only in this stage.
For discipline eligibility, a current official area label qualifies when it
case-insensitively contains the primary discipline or any supplied variant term.
For rank eligibility, include a candidate when the verified current rank matches ANY
of the effective included ranks, then apply all effective exclusions above.
Standardize the discipline output to exactly: {discipline}
"""
    allowed_domains = _domain_filters(roster["roster_source"], official_domains)
    web_tool: dict[str, Any] = {
        "type": "web_search",
        "filters": {
            "blocked_domains": [
                "wikipedia.org", "linkedin.com", "signalhire.com",
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
        text={"format": {
            "type": "json_schema",
            "name": "verified_faculty_classifications",
            "strict": True,
            "schema": SCHOOL_RESULT_SCHEMA,
        }},
        max_output_tokens=18000,
    )
    result = _parse_json_response(response, stage="Candidate verification")
    result["roster_source"] = roster["roster_source"]
    _apply_rank_guardrails(result, canonical_ranks=canonical_ranks)
    _validate_school_result(
        result,
        requested_school=school,
        roster_members=roster_members,
    )
    return result


def enrich_from_personal_websites(
    *,
    client: OpenAI,
    model: str,
    school: str,
    result: dict[str, Any],
) -> dict[str, Any]:
    included = [
        person for person in result["faculty_classifications"]
        if person["decision"] == "included"
    ]
    if not included:
        return result

    closed_candidates = [
        {
            "candidate_name": p["candidate_name"],
            "current_rank": p["current_rank"],
            "official_phd_year": p["phd_year"],
            "official_first_year_of_rank": p["first_year_of_rank"],
            "official_profile_or_cv_url": p["profile_or_cv_url"],
        }
        for p in included
    ]
    request = f"""
School: {school}

CLOSED LIST OF ALREADY-VERIFIED CANDIDATES:
{json.dumps(closed_candidates, ensure_ascii=False, indent=2)}

Search personal academic websites and personal CVs for supplemental biographical
information. Do not change eligibility/current rank. Return every supplied name
exactly once, even when no supplemental information is found.
"""
    response = client.responses.create(
        model=model,
        reasoning={"effort": "medium"},
        tools=[{
            "type": "web_search",
            "filters": {
                "blocked_domains": [
                    "wikipedia.org", "linkedin.com", "signalhire.com",
                    "researchgate.net", "zoominfo.com", "rocketreach.co",
                ]
            },
        }],
        tool_choice="required",
        include=["web_search_call.action.sources"],
        input=[
            {"role": "system", "content": SUPPLEMENTAL_SYSTEM_PROTOCOL},
            {"role": "user", "content": request},
        ],
        text={"format": {
            "type": "json_schema",
            "name": "supplemental_candidate_data",
            "strict": True,
            "schema": SUPPLEMENTAL_RESULT_SCHEMA,
        }},
        max_output_tokens=10000,
    )
    supplemental = _parse_json_response(response, stage="Personal-site enrichment")
    _validate_supplemental(supplemental, included)
    supplemental_by_name = {
        _normalized_name(x["candidate_name"]): x
        for x in supplemental["supplemental_records"]
    }

    for person in result["faculty_classifications"]:
        if person["decision"] != "included":
            continue
        extra = supplemental_by_name[_normalized_name(person["candidate_name"])]
        filled = []
        if person["phd_year"] is None and extra["phd_year"] is not None:
            person["phd_year"] = extra["phd_year"]
            filled.append("Ph.D. year")
        if person["first_year_of_rank"] is None and extra["first_year_of_rank"] is not None:
            person["first_year_of_rank"] = extra["first_year_of_rank"]
            person["first_year_basis"] = extra["first_year_basis"]
            if person["confidence"] == "high":
                person["confidence"] = "medium"
            filled.append("first year of rank")
        if extra["cv_url"]:
            # Prefer a discovered personal CV/academic CV page over a generic
            # profile link, while keeping the official current_source untouched.
            person["profile_or_cv_url"] = extra["cv_url"]
            filled.append("CV link")
        for url in extra["evidence_urls"]:
            if url and url not in person["evidence_urls"]:
                person["evidence_urls"].append(url)
        if filled:
            suffix = (
                "Supplemental personal academic source filled: "
                + ", ".join(filled)
                + "."
            )
            person["notes"] = f"{person['notes']} {suffix} {extra['notes']}".strip()

    result["school_note"] = (
        f"{result['school_note']} Personal academic websites were searched only "
        "for supplemental biographical fields; official sources controlled eligibility."
    ).strip()
    return result


def research_school(
    *,
    school: str,
    discipline: str,
    discipline_variants: list[str],
    included_rank: str,
    exclusions: list[str],
    current_only: bool = True,
    official_only: bool = True,
    allow_personal_websites: bool = True,
    model: str | None = None,
    roster_url: str = "",
) -> dict[str, Any]:
    if not os.getenv("OPENAI_API_KEY"):
        raise ResearchError("OPENAI_API_KEY is not configured.")
    if not current_only:
        raise ResearchError("Version 0.5 currently supports current faculty only.")
    if not official_only:
        raise ResearchError("Official sources must control current eligibility.")

    client = OpenAI()
    selected_model = model or os.getenv("OPENAI_MODEL", "gpt-5.6")
    configured = resolve_known_school(school) if not roster_url else None
    labels = discipline_labels(discipline, discipline_variants)
    configured_domains = configured.official_domains if configured else ()
    preferred_roster_url = roster_url
    if not preferred_roster_url and configured and configured.roster_url_supports(labels):
        preferred_roster_url = configured.roster_url

    resolution_method = (
        "user-supplied roster URL" if roster_url
        else "built-in tested roster URL" if preferred_roster_url
        else "registry-guided official-domain discovery" if configured
        else "automatic web discovery"
    )

    roster = discover_current_roster(
        client=client,
        model=selected_model,
        school=school,
        discipline=discipline,
        discipline_variants=discipline_variants,
        roster_url=preferred_roster_url,
        official_domains=configured_domains,
    )
    if roster["roster_status"] == "incomplete" and configured is not None and not roster_url:
        # Retry without a fixed URL but stay inside the school's explicit official
        # domains. This is especially important for international institutions.
        roster = discover_current_roster(
            client=client,
            model=selected_model,
            school=school,
            discipline=discipline,
            discipline_variants=discipline_variants,
            roster_url="",
            official_domains=configured_domains,
        )
        resolution_method = "registry-guided domain discovery after URL fallback"

        # Last resort: if the configured domain set itself is stale, allow the
        # model to rediscover an official source. The strict roster protocol still
        # forbids using non-current research/news pages as the roster.
        if roster["roster_status"] == "incomplete":
            roster = discover_current_roster(
                client=client,
                model=selected_model,
                school=school,
                discipline=discipline,
                discipline_variants=discipline_variants,
                roster_url="",
                official_domains=(),
            )
            resolution_method = "automatic official-source discovery after domain fallback"

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
        discipline_variants=discipline_variants,
        included_rank=included_rank,
        exclusions=exclusions,
        roster=roster,
        official_domains=configured_domains,
    )
    result["school_note"] = (
        f"Roster source selected by {resolution_method}. {result['school_note']}"
    ).strip()

    if allow_personal_websites:
        result = enrich_from_personal_websites(
            client=client,
            model=selected_model,
            school=school,
            result=result,
        )
    return result



def _standard_professor_rank(current_rank: str) -> str | None:
    """Return one of the three standard professor ranks when title text is clear."""
    rank_key = " ".join(str(current_rank).casefold().split())
    if "assistant professor" in rank_key:
        return "Assistant Professor"
    if "associate professor" in rank_key:
        return "Associate Professor"

    # Avoid treating clearly non-standard appointment types as Full Professor.
    nonstandard = (
        "professor of practice",
        "clinical professor",
        "research professor",
        "visiting professor",
        "teaching professor",
        "adjunct professor",
        "emeritus professor",
        "emerita professor",
    )
    if "professor" in rank_key and not any(term in rank_key for term in nonstandard):
        return "Full Professor"
    return None


def _apply_rank_guardrails(
    result: dict[str, Any],
    *,
    canonical_ranks: list[str],
) -> None:
    """Prevent obvious inclusion of a standard professor rank not requested."""
    requested = {rank.casefold() for rank in canonical_ranks}

    for person in result.get("faculty_classifications", []):
        if person.get("decision") != "included":
            continue
        standard_rank = _standard_professor_rank(person.get("current_rank", ""))
        if standard_rank is None or standard_rank.casefold() in requested:
            continue

        person["decision"] = "excluded"
        person["exclusion_or_review_reason"] = (
            f"Rank guardrail: verified current rank is {standard_rank}, which was "
            "not one of the requested ranks."
        )
        guardrail_note = (
            "Python rank guardrail changed an included classification to excluded "
            "because its verified standard professor rank was not requested."
        )
        person["notes"] = f"{person.get('notes', '')} {guardrail_note}".strip()

def _validate_roster(roster: dict[str, Any], *, requested_school: str) -> None:
    required = {
        "school_name", "discipline", "roster_source", "roster_status",
        "roster_note", "roster_members",
    }
    missing = required.difference(roster)
    if missing:
        raise ResearchError(f"Roster fields missing: {sorted(missing)}")
    if roster["roster_status"] == "completed":
        if not roster["roster_source"]:
            raise ResearchError(f"{requested_school}: completed roster has no source URL.")
        if not roster["roster_members"]:
            raise ResearchError(f"{requested_school}: completed roster contains no members.")
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
        _normalized_name(member["name"]): member for member in roster_members
    }
    output_names = [
        _normalized_name(person["candidate_name"])
        for person in result["faculty_classifications"]
    ]
    extras = sorted(set(output_names).difference(roster_by_name))
    missing = sorted(set(roster_by_name).difference(output_names))
    if extras:
        raise ResearchError(
            f"{requested_school}: model added names outside the current roster: {extras}"
        )
    if missing:
        raise ResearchError(
            f"{requested_school}: model failed to classify roster members: {missing}"
        )
    if len(output_names) != len(set(output_names)):
        raise ResearchError(f"{requested_school}: duplicate faculty classifications found.")
    for person in result["faculty_classifications"]:
        if person["decision"] == "included" and not person["current_source"]:
            raise ResearchError(
                f"{requested_school}: included candidate {person['candidate_name']} "
                "has no current official source."
            )


def _validate_supplemental(
    supplemental: dict[str, Any],
    included: list[dict[str, Any]],
) -> None:
    records = supplemental.get("supplemental_records")
    if not isinstance(records, list):
        raise ResearchError("supplemental_records must be a list.")
    expected = {_normalized_name(p["candidate_name"]) for p in included}
    actual = [_normalized_name(r["candidate_name"]) for r in records]
    extras = sorted(set(actual).difference(expected))
    missing = sorted(expected.difference(actual))
    if extras:
        raise ResearchError(f"Personal-site enrichment added unknown candidates: {extras}")
    if missing:
        raise ResearchError(f"Personal-site enrichment omitted candidates: {missing}")
    if len(actual) != len(set(actual)):
        raise ResearchError("Personal-site enrichment returned duplicate candidates.")
