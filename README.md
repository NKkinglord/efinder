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
