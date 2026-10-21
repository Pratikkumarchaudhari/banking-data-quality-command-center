# Banking Data Quality Monitoring Dashboard

A repeatable control layer for institution records: seven rules, weighted quality scores, ownership routing, and a reviewable exception queue.

**[Dashboard details and interview guide](docs/DASHBOARD_GUIDE.md)** — platform, rule definitions, column coverage, failure counts, denominators, and record investigation.

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

Running `pipeline.py` regenerates CSV/JSON outputs **and** the standalone `report.html` from the same evaluated data. Open the regenerated report to inspect a new input. `python render_report.py` can also rebuild the HTML from the saved outputs. The published website shows the checked-in sample snapshot; it is not connected to a live bank system. No server, account, or paid API is required. Normal internet and electricity use still apply.

```powershell
.\.venv\Scripts\python.exe pipeline.py --input local_data/institutions.csv --as-of 2026-09-30
```

## Platform and monitoring detail

| Component | Actual implementation |
|---|---|
| Rule authoring and execution | Python definitions and `evaluate()` in `pipeline.py`, using Pandas, Python date parsing, counters, and regex |
| Source | Deterministic synthetic sample, or a user-supplied CSV |
| Schema | 7 required source columns; 6 have quality rules; `bureau` is grouping/routing context |
| Quality dimensions | Completeness, validity, uniqueness, and timeliness |
| Result storage | `outputs/scored_records.csv`, `outputs/exceptions.csv`, `outputs/summary.json` |
| Report rendering | `render_report.py` + `report_template.html` + `dashboard.js` produce standalone HTML |
| SQL | SQLite-compatible reference queries, not the engine used for report metrics |
| Snowflake / dbt / Tableau | Possible future integrations; not deployed in this implementation |

The dashboard exposes per-rule logic, policy weight, pass/fail status and counts; per-column missing/distinct values and rule coverage; dimension totals; failed values and expectations; bureau/column/dimension/rule/weight/search filters; record drill-down; and filtered CSV export. A not-assessed column has no quality pass rate.

## Reproduced sample findings

250 synthetic records; 67 exceptions affecting 62 records; 96.17% rule-check pass rate. No remediation or employer impact is claimed.

| Rule | Source column | Failed checks / 250 |
|---|---|---:|
| DQ001 — required name | `name` | 15 |
| DQ002 — email syntax | `email` | 23 |
| DQ003 — supported state | `state` | 9 |
| DQ004 — recognized status | `license_status` | 7 |
| DQ005 — unique identifier | `institution_id` | 2 |
| DQ006 — verification recency | `last_verified` | 11 |
| DQ007 — nonblank identifier | `institution_id` | 0 |

Total: 1,750 checks = 1,683 passed + 67 failed. Six rule definitions have at least one violation and one passes every row. There are 62 affected source rows and 188 rows with no failures. These counts are different denominators, not interchangeable quality metrics.

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
| `report_template.html`, `dashboard.js`, `render_report.py` | Report source and automatic regeneration |
| `docs/DASHBOARD_GUIDE.md` | Granular platform, rule, column, and investigation walkthrough |
| `docs/INTERVIEW_GUIDE.md` | Walkthrough, decisions, limitations, resume wording |
| `.github/workflows/checks.yml` | Dependency install, unit checks, and sample execution |

## Data dictionary

institution_id: synthetic record key; name: institution name; bureau: routing label; email: example.org contact; state: supported two-letter jurisdiction code; license_status: Active/Surrendered/Suspended; last_verified: ISO date. Outputs retain row_number to disambiguate duplicated identifiers.

## Scope and limitations

Email checks validate syntax, not deliverability. State checks validate the code, not the address. Recency is a configurable policy. Bureau names are fictional labels. Snowflake/dbt/Tableau integrations are future adaptations; current executable stack is Python/Pandas plus SQLite reference SQL and a static HTML report.

Independent portfolio work developed with AI assistance. Contains no employer records, internal procedures, credentials, or confidential material. Synthetic benchmark results must not be presented as employer outcomes. Review and understand the implementation before representing it in an interview. MIT license covers this original code and synthetic data; separately imported source data retains its own terms.
