import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from pipeline import sample,evaluate
import render_report

class GranularityTests(unittest.TestCase):
    def test_column_and_dimension_denominators_reconcile(self):
        _,exc,s=evaluate(sample())
        self.assertEqual(s['input_columns'],7)
        self.assertEqual(s['evaluated_columns'],6)
        self.assertEqual(sum(r['checked'] for r in s['rule_catalog']),s['rule_checks'])
        self.assertEqual(sum(r['failed'] for r in s['rule_catalog']),len(exc))
        self.assertEqual(sum(d['failed'] for d in s['dimension_results']),len(exc))
        self.assertEqual(sum(c['failed_checks'] for c in s['column_profiles']),len(exc))
        self.assertEqual(s['rules_failed'],6)
        self.assertEqual(s['passed_checks'],1683)
        cols={c['column']:c for c in s['column_profiles']}
        self.assertIsNone(cols['bureau']['pass_rate'])
        self.assertEqual(cols['bureau']['rule_checks'],0)
        self.assertEqual(cols['institution_id']['rule_checks'],500)
        self.assertEqual(cols['institution_id']['affected_records'],2)
    def test_observed_values_trace_to_normalized_source_rows(self):
        records,exc,s=evaluate(sample())
        for e in exc.to_dict('records'):
            record=records.iloc[e['row_number']-1]
            self.assertEqual(e['observed_value'],record[e['column']])
            self.assertTrue(e['expected'])
        self.assertEqual(exc[exc.rule=='valid_email'].observed_value.unique().tolist(),['invalid-email'])
    def test_clean_sample_keeps_all_pass_rules_and_zero_exceptions(self):
        _,exc,s=evaluate(sample().iloc[1:2].copy())
        self.assertTrue(exc.empty)
        self.assertEqual(s['rules_failed'],0)
        self.assertEqual(s['rules_passed'],7)
        self.assertEqual(s['passed_checks'],7)
        self.assertEqual(s['passed_records'],1)
    def test_extra_input_columns_are_not_misrepresented_as_validated(self):
        df=sample().iloc[1:2].copy();df['extra_context']='x'
        _,_,s=evaluate(df)
        self.assertEqual(s['input_columns'],8)
        self.assertEqual(s['evaluated_columns'],6)
        self.assertIsNone(s['column_profiles'][-1]['pass_rate'])
    def test_report_escapes_script_terminators_and_template_markers(self):
        df=sample().iloc[1:2].copy();df['name']='</script><script>alert(1)</script> __DQ_SCRIPT__'
        records,exc,s=evaluate(df)
        original_root=render_report.ROOT
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder)
            for name in ['report_template.html','dashboard.js']:shutil.copyfile(original_root/name,folder/name)
            with patch.object(render_report,'ROOT',folder):out=render_report.write_report(records,exc,s)
            match=re.search(r'<script id="dq-data" type="application/json">(.*?)</script>',out,re.S)
            payload=json.loads(match.group(1))
            self.assertEqual(payload['records'][0]['name'],df.iloc[0]['name'])
            self.assertNotIn('</script>',match.group(1))

if __name__=='__main__':unittest.main()
