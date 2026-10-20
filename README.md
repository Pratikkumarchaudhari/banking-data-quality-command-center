# Banking Data Quality Monitoring Dashboard

A repeatable control layer for institution records: seven rules, weighted quality scores, ownership routing, and a reviewable exception queue.

**[Open the interactive demo](https://pratikkumar-data-ai-portfolio.woollydog11.chatgpt.site/demos/banking-data-quality-command-center.html)** · [Portfolio](https://pratikkumar-data-ai-portfolio.woollydog11.chatgpt.site) · [LinkedIn](https://www.linkedin.com/in/pratikkumarchaudhari/)

## Business question

Which institution records need attention, which rules failed, and which team should review them?

## Run locally — no paid APIs or cloud account

Requires Python 3.11 or 3.12. In Windows PowerShell:

```powershell
git clone https://github.com/Pratikkumarchaudhari/banking-data-quality-command-center.git
cd banking-data-quality-command-center
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe pipeline.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
Start-Process report.html
```

On macOS/Linux use `python3 -m venv .venv`, `.venv/bin/python -m pip install -r requirements.txt`, then `.venv/bin/python pipeline.py`. Open `report.html` in your browser.

`report.html` is a checked-in snapshot of the demonstrated sample results. Running the command regenerates CSV/JSON outputs; it does not automatically refresh the HTML. For a new input, inspect those generated outputs or explicitly rebuild the report. No server, account, or API key is required. Normal internet and electricity use still apply.

## Reproduced sample findings

250 synthetic records; 67 exceptions affecting 62 records; 96.17% rule-check pass rate. No remediation or employer impact is claimed.

## How it works

Validate the input schema → trim strings → evaluate seven rules → preserve every input row → emit scored records and one exception per failed rule → reconcile summary denominators. Duplicate IDs flag both rows rather than hiding a problem by dropping one. Evaluation is anchored to 2026-09-30, with a configurable --as-of date.

Weights (illustrative policy choices): name 3, email 2, state 2, status 3, uniqueness 4, timeliness 1, identifier validity 4. Weighted score = 100 × (1 − failed weight / total weight). Rule-check pass rate = 100 × passed checks / all checks. Neither score proves business correctness.

## Repository guide

| Path | Purpose |
|---|---|
| `pipeline.py` | Executable analysis pipeline |
| `outputs/` | Reproducible sample metrics and review outputs |
| `tests/` | Meaningful input, reconciliation, and behavior checks |
| `report.html` | Standalone interactive sample report |
| `docs/INTERVIEW_GUIDE.md` | Walkthrough, decisions, limitations, resume wording |
| `.github/workflows/checks.yml` | Dependency install, unit checks, and sample execution |

## Data dictionary

institution_id: synthetic record key; name: institution name; bureau: routing label; email: example.org contact; state: supported two-letter jurisdiction code; license_status: Active/Surrendered/Suspended; last_verified: ISO date. Outputs retain row_number to disambiguate duplicated identifiers.

## Scope and limitations

Email checks validate syntax, not deliverability. State checks validate the code, not the address. Recency is a configurable policy. Bureau names are fictional labels. Snowflake/dbt/Tableau integrations are future adaptations; current executable stack is Python/Pandas plus SQLite reference SQL and a static HTML report.

Independent portfolio work developed with AI assistance. Contains no employer records, internal procedures, credentials, or confidential material. Synthetic benchmark results must not be presented as employer outcomes. Review and understand the implementation before representing it in an interview. MIT license covers this original code and synthetic data; separately imported source data retains its own terms.
