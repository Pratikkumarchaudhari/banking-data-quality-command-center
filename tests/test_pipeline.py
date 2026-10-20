import unittest
from datetime import date
import pandas as pd
from pipeline import sample,evaluate

class QualityTests(unittest.TestCase):
    def test_duplicate_flags_both_rows(self):
        df=sample().iloc[1:3].copy();df['institution_id']='SAME'
        _,exc,_=evaluate(df)
        self.assertEqual((exc.rule=='unique_id').sum(),2)
    def test_future_and_malformed_dates(self):
        df=sample().iloc[1:3].copy();df['last_verified']=['2027-01-01','bad']
        _,exc,_=evaluate(df)
        self.assertEqual((exc.rule=='fresh_record').sum(),2)
    def test_empty_and_missing_schema(self):
        with self.assertRaises(ValueError):evaluate(pd.DataFrame())
        with self.assertRaises(ValueError):evaluate(sample().iloc[:0])
    def test_clean_record_and_missing_id(self):
        df=sample().iloc[1:2].copy()
        _,exc,s=evaluate(df);self.assertEqual(len(exc),0);self.assertEqual(s['pass_rate'],100)
        df['institution_id']='';_,exc,_=evaluate(df)
        self.assertIn('valid_id',exc.rule.tolist())
    def test_reconciles_denominator(self):
        _,exc,s=evaluate(sample())
        self.assertEqual(s['exceptions'],len(exc))
        self.assertEqual(s['pass_rate'],round(100*(1-len(exc)/s['rule_checks']),2))
if __name__=='__main__':unittest.main()
