from __future__ import annotations

from urllib.parse import urlparse


def discipline_labels(discipline: str, variants: list[str]) -> list[str]:
    """Return the primary discipline plus unique user-entered search terms."""
    labels = []
    seen = set()
    for value in [discipline, *variants]:
        cleaned = " ".join(value.strip().split())
        if cleaned and cleaned.casefold() not in seen:
            seen.add(cleaned.casefold())
            labels.append(cleaned)
    return labels


def parse_discipline_variants(value: str) -> list[str]:
    """Parse the UI discipline-variant field using commas as the delimiter."""
    seen = set()
    output = []
    for part in value.split(","):
        cleaned = " ".join(part.strip().split())
        key = cleaned.casefold()
        if cleaned and key not in seen:
            seen.add(key)
            output.append(cleaned)
    return output


def parse_rank_terms(value: str) -> list[str]:
    """Parse comma-separated requested faculty ranks and canonicalize common names.

    `Professor` and `Full Professor` are the same requested rank. Other rank
    labels are preserved after whitespace cleanup so the model can apply them
    semantically.
    """
    output: list[str] = []
    seen = set()
    for part in value.split(","):
        cleaned = " ".join(part.strip().split())
        if not cleaned:
            continue
        if cleaned.casefold() in {"professor", "full professor"}:
            cleaned = "Full Professor"
        key = cleaned.casefold()
        if key not in seen:
            seen.add(key)
            output.append(cleaned)
    return output


def resolve_rank_search_rules(
    included_rank: str,
    exclusions: list[str],
) -> tuple[list[str], list[str], list[str]]:
    """Resolve multi-rank search semantics and safe automatic exclusions.

    The UI accepts comma-separated ranks. `Professor` means Full Professor.
    When Full Professor is requested, Assistant/Associate Professor are added
    as automatic exclusions only when those ranks were NOT explicitly included.
    User-selected exclusions are always preserved.
    """
    canonical_ranks = parse_rank_terms(included_rank)
    requested = {rank.casefold() for rank in canonical_ranks}

    automatic_exclusions: list[str] = []
    if "full professor" in requested:
        if "assistant professor" not in requested:
            automatic_exclusions.append("Assistant Professor")
        if "associate professor" not in requested:
            automatic_exclusions.append("Associate Professor")

    effective_exclusions: list[str] = []
    seen = set()
    for value in [*exclusions, *automatic_exclusions]:
        cleaned = " ".join(str(value).strip().split())
        key = cleaned.casefold()
        if cleaned and key not in seen:
            seen.add(key)
            effective_exclusions.append(cleaned)

    return canonical_ranks, automatic_exclusions, effective_exclusions

def safe_search_domains(
    roster_url: str = "",
    configured_domains: tuple[str, ...] | list[str] = (),
) -> list[str]:
    """Return institution-level domains without collapsing public suffixes.

    Known schools supply explicit official domains. For an unknown school, only
    the exact roster hostname (and the same hostname without `www.`) is used.
    This intentionally avoids unsafe reductions such as `jbs.cam.ac.uk` ->
    `ac.uk` or `nus.edu.sg` -> `edu.sg`.
    """
    domains: list[str] = []
    for domain in configured_domains:
        cleaned = str(domain).strip().lower().lstrip(".")
        if cleaned.startswith("www."):
            cleaned = cleaned[4:]
        if cleaned and cleaned not in domains:
            domains.append(cleaned)

    hostname = (urlparse(roster_url).hostname or "").lower()
    if hostname:
        host_no_www = hostname[4:] if hostname.startswith("www.") else hostname
        for value in (hostname, host_no_www):
            if value and value not in domains:
                domains.append(value)
    return domains
