# Faculty Research Agent v0.3 / Strict Roster Starter

This is a no-login, no-database Streamlit prototype.

It asks for:

- Discipline or area
- Included rank
- Current faculty only
- Excluded appointment types
- A pasted or uploaded CSV school list

It then runs one official-source web research request per school and generates
an Excel workbook with:

- Candidates
- Needs Review
- School Summary
- Source Audit
- Run Configuration

## 1. Requirements

- Python 3.11 or newer
- An OpenAI API key
- Internet access

## 2. Create an API key

Create an API key in the OpenAI Platform dashboard. Do not place the key
directly in the Python source code.

## 3. Set up locally

### macOS / Linux

```bash
cd faculty-research-agent-starter
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and replace:

```text
OPENAI_API_KEY=replace_with_your_api_key
```

Then run:

```bash
streamlit run app.py
```

### Windows PowerShell

```powershell
cd faculty-research-agent-starter
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env`, add the API key, and run:

```powershell
streamlit run app.py
```

## 4. First test

Do not begin with all 23 schools.

Start with:

1. Duke University (Fuqua)
2. University of Florida (Warrington)
3. Northwestern University (Kellogg)

These schools test:

- A normal current associate-professor roster
- Ambiguous "Term" titles
- A legitimate zero-candidate result

Set **Maximum schools for this run** to `1` for the first API test.

## 5. Input CSV

The easiest format is:

```csv
School Name
Duke University (Fuqua)
University of Florida (Warrington)
```

The app also accepts a CSV whose school names are in the first column.

## 6. Run the smoke test without using the API

```bash
python smoke_test.py
```

This verifies school parsing and Excel generation.

## Important limitations of Version 0.1

- It uses one model research call per school.
- It does not persist progress if the browser session closes.
- It does not retry failed schools automatically.
- It accepts CSV or pasted input, not XLSX input yet.
- It has no authentication.
- It should be validated against manually checked schools before office use.
- A later version should separate roster discovery and candidate verification
  into two API stages for stronger completeness checks.


## Strict roster change in v0.3

The original prototype could include a person mentioned on an old official
research or Ph.D. page even when the person was absent from the current faculty
roster.

Version 0.3 uses two API stages:

1. Discover the exact current official roster.
2. Verify only the names in that closed roster list.

The Python validator rejects any name added outside the discovered roster and
requires every roster member to be classified exactly once.

If the current roster page is dynamic or cannot be read, the school is marked
`incomplete`; the application does not infer candidates from related pages.

For the safest run, provide an `Official Roster URL` column in the CSV:

```csv
School Name,Official Roster URL
Duke University (Fuqua),https://areas.fuqua.duke.edu/accounting/
```

You may also paste:

```text
Duke University (Fuqua) | https://areas.fuqua.duke.edu/accounting/
```

This version uses two API calls per completed school, so it costs more than
version 0.1 but is substantially safer.

## Automatic roster selection in v0.3

You now normally enter only the school name:

```text
Duke University (Fuqua)
```

The app has a built-in registry for the original 23 business schools and uses
Duke's readable current full faculty directory automatically. School aliases
such as `Duke`, `Duke Fuqua`, and `Fuqua` also resolve to the same configured
school.

For a school not in the registry, the app asks the web-search stage to locate a
current official roster. If a saved roster URL is no longer readable, the app
tries automatic discovery once before marking the school incomplete.

An optional `Official Roster URL` CSV column and the `School | URL` pasted
format remain available as advanced overrides, but they are not required.


## Version 0.4 changes

- Renamed the interface to **Peer Scholars Search Tool**.
- Added **Variants of name** under Discipline. Enter comma-separated equivalents, for example `Accountancy` for Accounting or `Decision and Operations` for Operations Management.
- Current eligibility remains official-source-only.
- Added optional **personal academic website enrichment** for missing Ph.D. year, first-year-of-rank, and CV link.
- Personal websites cannot add candidates, change current rank, or override official current affiliation.
- Wikipedia, LinkedIn, commercial people-search sites, and ResearchGate are not accepted as supplemental evidence.

Because personal-site enrichment is a separate web-search stage, enabling it can add one additional API call per school that has included candidates.

## v0.4.2: flexible school-name matching

Known schools no longer require an exact alias. Harmless wording differences such as
`Duke University (Fuqua School of Business)`, `Duke University (Fuqua)`, and
`Fuqua School of Business` resolve to the same tested current Fuqua directory.
The matcher is conservative: if a name could refer to more than one institution,
it does not guess and instead uses automatic web discovery.


## v0.4.3 strong school aliases

The school registry now supports distinctive "strong aliases."

For Duke University (Fuqua), either standalone word below is sufficient:

- `duke`
- `fuqua`

Therefore inputs such as these all resolve to the tested Fuqua roster URL:

```text
Duke
Duke University (Fuqua School of Business)
current accounting faculty at Duke
Fuqua accounting
peer list - FUQUA - current faculty
```

Strong aliases use normalized whole words, so unrelated strings such as
`Dukes County` do not match `duke`.

Later releases expand this mechanism to common abbreviations within the
configured school universe, with longest-match-wins disambiguation.

## v0.4.4 common school aliases

The 23-school registry now accepts common shorthand directly.

Examples:

- USC / Marshall -> University of Southern California (Marshall)
- UT / UT Austin / McCombs -> University of Texas at Austin (McCombs)
- UW / Foster -> University of Washington (Foster)
- UCLA / Anderson
- NYU / Stern
- MIT / Sloan
- UNC / Kenan-Flagler
- IU / Kelley
- UIUC / Gies
- UF / Warrington
- UGA / Terry
- PSU / Smeal
- WashU / WUSTL / Olin
- UMich / Michigan / Ross
- UCB / Berkeley / Haas

These abbreviations are interpreted inside the application's configured school
universe. If the registry is later expanded to include another school using the
same abbreviation, the alias should be revised to avoid ambiguity.


## v0.5.0 global top-100 registry

The built-in resolver now covers the QS Global MBA Rankings 2026 rank-through-99
cohort. Because the cutoff has ties, that is 101 ranked schools. The original
University of Illinois (Gies) and University of Georgia (Terry) records are also
retained, for 103 built-in school records total.

International schools are first-class registry entries. Each known school can
carry explicit official domains such as `cam.ac.uk`, `nus.edu.sg`, `hkust.edu.hk`,
`iimb.ac.in`, `uct.ac.za`, `uq.edu.au`, and `qu.edu.qa`. The search code no longer
assumes that an official university domain ends in `.edu`.

For schools that have no tested roster URL, the app automatically searches only
inside that school's configured official domains first. If the domain configuration
is stale, it can perform one final strict official-source discovery pass.

Saved roster URLs can now be discipline-specific. For example, an Accounting page
is used for Accounting/Accountancy, but not incorrectly reused for Operations or
Finance.
