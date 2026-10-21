# Validation

Executed in Python 3.12 in the portfolio build workspace. Dependency versions are recorded in requirements.txt.

- `pipeline.py` completed and wrote the checked-in sample outputs.
- Python unit tests passed: 10.
- Sample result: 250 synthetic records; 67 exceptions affecting 62 records; 96.17% rule-check pass rate. No remediation or employer impact is claimed.
- Four Node dashboard-logic tests passed with `node --test tests/dashboard.test.cjs`.
- The pipeline regenerates its CSV/JSON outputs and standalone HTML report from the same evaluation.
- Rule, column, and dimension counts reconcile; exception values trace to normalized source rows.
- The report provides rule logic, column coverage, combined filters, record drill-down, and filtered CSV export.
- Browser interaction and Windows commands were not executed in this workspace.
- GitHub Actions has been configured; its remote run is not claimed here.

This validates the sample computation, not external source accuracy or production readiness.
