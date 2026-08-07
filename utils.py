from urllib.parse import urlparse


def discipline_labels(discipline: str, variants: list[str]) -> list[str]:
    labels = []
    seen = set()
    for value in [discipline, *variants]:
        cleaned = " ".join(value.strip().split())
        if cleaned and cleaned.casefold() not in seen:
            seen.add(cleaned.casefold())
            labels.append(cleaned)
    return labels


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
