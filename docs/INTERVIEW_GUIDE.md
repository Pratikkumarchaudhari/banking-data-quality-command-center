# Interview walkthrough: Banking Data Quality Monitoring Dashboard

For rule-level definitions, platform details, column coverage, and record investigation, read the [Dashboard details guide](DASHBOARD_GUIDE.md).

## 60-second explanation

“This is an independent portfolio project connecting my data stewardship experience with hands-on Python analysis. The question is: which records should a steward investigate first? I used synthetic data so the work is reproducible and shareable. 250 synthetic records; 67 exceptions affecting 62 records; 96.17% rule-check pass rate. No remediation or employer impact is claimed. I would validate the assumptions and outputs with a business owner before applying the method to real data.”

## Demonstrate it in five minutes

1. Show the business question and data dictionary in the README.
2. Open `report.html`; use the filter and explain the denominator or model threshold.
3. Trace one row through the executable Python code into the CSV/JSON output.
4. Run the tests and explain one edge case that could change the conclusion.
5. Discuss a limitation below and propose a measured next experiment.

## Architecture and tradeoffs

Validate the input schema → trim strings → evaluate seven rules → preserve every input row → emit scored records and one exception per failed rule → reconcile summary denominators. Duplicate IDs flag both rows rather than hiding a problem by dropping one. Evaluation is anchored to 2026-09-30, with a configurable --as-of date.

Weights (illustrative policy choices): name 3, email 2, state 2, status 3, uniqueness 4, timeliness 1, identifier validity 4. Weighted score = 100 × (1 − failed weight / total weight). Rule-check pass rate = 100 × passed checks / all checks. Neither score proves business correctness.

## What I would change for production

Add source contracts, versioned datasets, access control, approved retention, source-to-report lineage, observed business SLAs, independent review, and monitoring for changing inputs. Current implementation stays local and has no enterprise deployment. SQL examples in analytics projects can be adapted to a governed Snowflake/dbt pipeline; they are not deployed Snowflake integrations.

## Strong questions to be ready for

- How did you prevent bad keys or missing values from changing the result?
- What is the denominator of each published metric?
- Which design choice is policy rather than an empirical finding?
- Which result would make you choose a simpler approach?
- What did you verify locally, and what remains untested?

## Honest resume wording after reviewing the code

“Implemented and evaluated an independent banking data quality monitoring dashboard project using Python, reproducible synthetic data, automated validation, and an interactive results report.”

## Limits

Email checks validate syntax, not deliverability. State checks validate the code, not the address. Recency is a configurable policy. Bureau names are fictional labels. Snowflake/dbt/Tableau integrations are future adaptations; current executable stack is Python/Pandas plus SQLite reference SQL and a static HTML report.
