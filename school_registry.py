from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SchoolSource:
    canonical_name: str
    roster_url: str
    aliases: tuple[str, ...]


def _normalize(value: str) -> str:
    value = value.casefold()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


# These are preferred current official roster/directory pages. The research
# workflow still verifies the page and can fall back to automatic discovery if
# a saved URL is no longer usable.
SCHOOL_SOURCES: tuple[SchoolSource, ...] = (
    SchoolSource(
        "University of Pennsylvania (Wharton)",
        "https://accounting.wharton.upenn.edu/faculty/faculty-list/",
        ("wharton", "upenn wharton", "university of pennsylvania", "penn wharton"),
    ),
    SchoolSource(
        "Northwestern University (Kellogg)",
        "https://www.kellogg.northwestern.edu/faculty-research/faculty-directory/",
        ("kellogg", "northwestern kellogg", "northwestern university"),
    ),
    SchoolSource(
        "Stanford University",
        "https://www.gsb.stanford.edu/faculty-research/faculty/academic-areas/accounting",
        ("stanford", "stanford gsb", "stanford graduate school of business"),
    ),
    SchoolSource(
        "Massachusetts Institute of Technology (Sloan)",
        "https://mitsloan.mit.edu/faculty/academic-groups/accounting/faculty-research-centers",
        ("mit", "mit sloan", "massachusetts institute of technology", "sloan"),
    ),
    SchoolSource(
        "New York University (Stern)",
        "https://www.stern.nyu.edu/experience-stern/about/departments-centers-initiatives/academic-departments/accounting/faculty-staff/full-time-faculty",
        ("nyu", "nyu stern", "new york university", "stern"),
    ),
    SchoolSource(
        "Columbia University (Columbia Business School)",
        "https://business.columbia.edu/faculty/divisions/accounting/faculty",
        ("columbia", "columbia business school", "cbs"),
    ),
    SchoolSource(
        "University of California, Berkeley (Haas)",
        "https://haas.berkeley.edu/faculty-research/academic-groups/",
        ("berkeley haas", "uc berkeley", "haas", "university of california berkeley"),
    ),
    SchoolSource(
        "Duke University (Fuqua)",
        "https://www.fuqua.duke.edu/faculty-research/directory/all",
        ("duke", "duke fuqua", "fuqua", "duke university"),
    ),
    SchoolSource(
        "Cornell University (Johnson)",
        "https://business.cornell.edu/faculty-research/accounting/",
        ("cornell", "cornell johnson", "johnson", "cornell university"),
    ),
    SchoolSource(
        "University of California, Los Angeles (Anderson)",
        "https://www.anderson.ucla.edu/faculty-and-research/accounting/faculty",
        ("ucla", "ucla anderson", "anderson", "university of california los angeles"),
    ),
    SchoolSource(
        "University of Michigan (Ross)",
        "https://michiganross.umich.edu/faculty-research/areas-of-study/accounting",
        ("michigan ross", "university of michigan", "ross"),
    ),
    SchoolSource(
        "University of Notre Dame (Mendoza)",
        "https://mendoza.nd.edu/mendoza-directory/",
        ("notre dame", "notre dame mendoza", "mendoza", "university of notre dame"),
    ),
    SchoolSource(
        "Pennsylvania State University (Smeal)",
        "https://www.smeal.psu.edu/accounting/people/faculty",
        ("penn state", "penn state smeal", "smeal", "pennsylvania state university"),
    ),
    SchoolSource(
        "University of Southern California (Marshall)",
        "https://www.marshall.usc.edu/faculty-research/faculty-directory",
        ("usc marshall", "southern california marshall", "university of southern california", "marshall"),
    ),
    SchoolSource(
        "University of North Carolina at Chapel Hill (Kenan-Flagler)",
        "https://www.kenan-flagler.unc.edu/faculty/",
        ("unc", "unc chapel hill", "unc kenan flagler", "kenan flagler", "university of north carolina"),
    ),
    SchoolSource(
        "University of Washington (Foster)",
        "https://foster.uw.edu/faculty-research/academic-departments/accounting/faculty/",
        ("uw foster", "washington foster", "university of washington", "foster"),
    ),
    SchoolSource(
        "Indiana University (Kelley)",
        "https://kelley.iu.edu/faculty-research/faculty-directory/",
        ("indiana kelley", "indiana university", "iu kelley", "kelley"),
    ),
    SchoolSource(
        "University of Illinois Urbana-Champaign (Gies)",
        "https://giesbusiness.illinois.edu/faculty-research/faculty-profiles?department=BA",
        ("illinois gies", "uiuc", "university of illinois", "gies"),
    ),
    SchoolSource(
        "Rice University (Jones)",
        "https://business.rice.edu/faculty-research/academic-areas/accounting",
        ("rice", "rice jones", "jones graduate school", "rice university"),
    ),
    SchoolSource(
        "University of Florida (Warrington)",
        "https://warrington.ufl.edu/directory/",
        ("florida warrington", "university of florida", "uf warrington", "warrington"),
    ),
    SchoolSource(
        "Washington University in St. Louis (Olin)",
        "https://olin.wustl.edu/faculty-and-research/academic-areas/accounting/",
        ("washu olin", "washington university st louis", "washington university in st louis", "olin"),
    ),
    SchoolSource(
        "University of Georgia (Terry)",
        "https://www.terry.uga.edu/faculty-research/departments/accounting/",
        ("georgia terry", "university of georgia", "uga terry", "terry"),
    ),
    SchoolSource(
        "University of Texas at Austin (McCombs)",
        "https://www.mccombs.utexas.edu/faculty-and-research/faculty-directory/",
        ("ut austin", "texas mccombs", "university of texas", "mccombs"),
    ),
)


_ALIAS_INDEX: dict[str, SchoolSource] = {}
for source in SCHOOL_SOURCES:
    names = (source.canonical_name, *source.aliases)
    for name in names:
        key = _normalize(name)
        existing = _ALIAS_INDEX.get(key)
        if existing is not None and existing != source:
            raise RuntimeError(f"Duplicate school alias: {name}")
        _ALIAS_INDEX[key] = source


def resolve_known_school(school_name: str) -> SchoolSource | None:
    """Return a configured source only for a known, unambiguous alias."""
    return _ALIAS_INDEX.get(_normalize(school_name))
