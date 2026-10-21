# Banking Data Quality Dashboard — platform and investigation guide

[Open the dashboard](https://pratikkumar-data-ai-portfolio.woollydog11.chatgpt.site/demos/banking-data-quality-command-center.html) · [Project README](../README.md)

## Explain the platform in an interview

“This independent project runs seven explicit data-quality controls in Python/Pandas against a synthetic institution dataset. It writes scored records, exception evidence, and summarized outcomes to CSV/JSON, then renders a standalone dashboard. The report lets a reviewer trace a failed rule to its column, normalized value, expected condition, and source row. The SQL queries are reference examples; this version does not execute rules in Snowflake, dbt, or Tableau.”

## What the sample contains

| Item | Count / detail |
|---|---|
| Source rows | 250 |
| Input columns | 7 |
| Columns with quality rules | 6 |
| Context-only column | `bureau` |
| Rules | 7 |
| Dimensions assessed | 4 |
| As-of date | 2026-09-30 |
| Rule checks | 1,750 |
| Passed / failed checks | 1,683 / 67 |
| Affected / unaffected source rows | 62 / 188 |
| Rules with violations / fully passed rules | 6 / 1 |
| Check pass rate | 96.17% |
| Mean weighted score | 96.86 / 100 |

The sample names and bureau labels are fictional. These are not employer outcomes, an operational bank feed, or measured production remediation results.

## Rule catalog: definition, field, and sample result

| ID | Rule | Column | Dimension | Weight | Passed | Failed |
|---|---|---|---|---:|---:|---:|
| DQ001 | Trimmed name is nonblank | `name` | Completeness | 3 | 235 | 15 |
| DQ002 | Nonblank email matches a syntax regex, with no whitespace and a dotted domain | `email` | Validity | 2 | 227 | 23 |
| DQ003 | State is in the supported case-sensitive US jurisdiction-code set | `state` | Validity | 2 | 241 | 9 |
| DQ004 | Status is Active, Surrendered, or Suspended | `license_status` | Validity | 3 | 243 | 7 |
| DQ005 | Identifier occurs exactly once in this input | `institution_id` | Uniqueness | 4 | 248 | 2 |
| DQ006 | Parseable ISO date, with age between 0 and 90 days inclusive | `last_verified` | Timeliness | 1 | 239 | 11 |
| DQ007 | Trimmed identifier is nonblank | `institution_id` | Validity | 4 | 250 | 0 |

The executable rule predicates are in `pipeline.py:evaluate`. `RULES` and `RULE_DETAILS` describe the policy weights, names, fields, expected conditions, and recommended actions. Update the predicate and its metadata together when changing policy.

A “failed rule” in the dashboard means its execution found one or more violations. It does not mean a job crashed. Policy weights rank contributions to the illustrative score; they are not calibrated risk probabilities or regulatory severity categories.

## What does each source column mean?

| Column | Role | Coverage |
|---|---|---|
| `institution_id` | Institution identifier, which can contain a duplicate in the sample | Presence and uniqueness: two checks per row |
| `name` | Fictional institution name | Required-value check |
| `bureau` | Grouping and suggested routing label | No quality rule; not assessed |
| `email` | Example contact address | Syntax check only |
| `state` | US jurisdiction code | Membership in supported code set |
| `license_status` | Institution license status | Allowed-value check |
| `last_verified` | Verification date | Date parsing and recency check |

All input values are normalized to stripped strings, with null values replaced by blank strings. The schema gate checks that the required column names exist and rejects empty datasets. It does not establish that the source's business meaning or physical types are correct. Extra columns are retained as unassessed context.

The column profile shows missing counts, distinct counts (including a blank if present), assigned rule IDs, checks, failed checks, affected rows, and pass rate. `institution_id` contributes 500 checks because it has two rules. `bureau` contributes zero checks and has no pass rate; “not assessed” is different from “passed.”

## Walk through an actual failure

1. Open the rule catalog and expand DQ002's logic. It runs in Python/Pandas, not a Snowflake DMF.
2. Select its failure count: 23. The queue filters to that rule.
3. Observe `invalid-email` in the failed value column and compare it with the expected email condition.
4. Add a bureau filter to narrow the review queue. Filters combine with AND.
5. Select **Inspect row**. Review all source columns, the row's weighted score, and the outcomes of all seven controls.
6. Export the filtered CSV if a reviewer needs that subset. This is an evidence export, not an automated ticket or a remediation action.

For uniqueness, DQ005 flags both source rows sharing `SYN0019`. Source row numbers distinguish them; do not silently deduplicate or count two rows as two distinct institutions.

The observed value is the normalized value the rule evaluated. Original pre-normalization bytes are not retained in the report. A production audit design should decide whether it must retain both raw and normalized evidence.

## Understand the denominators

- **Checks:** rows × assigned rules. This sample has 250 × 7 = 1,750.
- **Failed checks:** one exception per failed rule on one row. Total 67.
- **Affected rows:** distinct source row numbers appearing in exceptions. Total 62.
- **Rules with violations:** rule definitions with at least one failed check. Total 6.
- **Column/dimension affected rows:** distinct rows failing any rule within that group. These counts overlap across groups and should not be summed as dataset-wide affected rows.
- **Check pass rate:** 100 × (1 − failed checks / evaluated checks).
- **Record weighted score:** 100 × (1 − sum of failed rule weights / 19). The dashboard averages record scores rounded to two decimals.

The overview remains scoped to the complete snapshot when queue filters change. The queue separately reports how many exceptions and distinct rows match the filters. A six-column coverage count does not mean that every possible quality property of those columns was checked.

## Data flow and refresh

`sample()` or CSV input → schema gate → string normalization → seven predicates per row → scored records + exceptions + rule/column/dimension summaries → CSV/JSON outputs → standalone HTML report.

`pipeline.py` now regenerates the HTML automatically. `render_report.py` can rebuild it from saved outputs. A SHA-256 fingerprint identifies the normalized dataset used for the saved snapshot. The as-of date controls recency; the published report does not continuously poll a source.

```powershell
python pipeline.py
python pipeline.py --input local_data/institutions.csv --as-of 2026-09-30
python render_report.py
python -m unittest discover -s tests -v
node --test tests/dashboard.test.cjs
```

Use the virtual-environment executable shown in the main README when applicable. Publishing new sample results requires publishing the regenerated report; running the pipeline locally does not automatically update the hosted site.

## Limits and possible next steps

Email syntax is not deliverability, and a supported state code is not a verified physical address. Accuracy and cross-source consistency are not measured. There is no live schedule, historical trend store, assigned reviewer account, SLA timer, or issue-management integration. The displayed bureau is a context label, not a functioning workflow engine.

Possible extensions are approved source ingestion, a governed warehouse, versioned rule deployments, historical run comparison, owner-reviewed weights, secure role-based access, and issue tracking. For a Snowflake implementation, map each predicate to an appropriate SQL test or DMF and validate equivalent results before describing it as deployed.

## Verification

Ten Python tests passed, including rule/column/dimension reconciliation, normalized evidence tracing, clean datasets, extra-column coverage, and safe HTML embedding. Four Node tests passed for combined filters, duplicate-row drill-down, observed-value search, and CSV escaping. These verify computation and dashboard logic. Browser interaction was not verified in the build workspace.
