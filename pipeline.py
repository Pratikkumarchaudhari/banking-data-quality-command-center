"""Deterministic banking-data quality rules and auditable exception output."""
import argparse
from collections import Counter
from datetime import date
from pathlib import Path
import json
import re
import pandas as pd

ROOT = Path(__file__).resolve().parent
AS_OF = date(2026, 9, 30)
RULES = {
    'required_name': ('Completeness', 3, 'Supply institution name'),
    'valid_email': ('Validity', 2, 'Confirm contact email'),
    'valid_state': ('Validity', 2, 'Use a supported two-letter state code'),
    'valid_status': ('Validity', 3, 'Review license status'),
    'unique_id': ('Uniqueness', 4, 'Resolve duplicate institution identifier'),
    'fresh_record': ('Timeliness', 1, 'Verify record within 90 days'),
    'valid_id': ('Validity', 4, 'Supply nonblank institution identifier'),
}
STATES = set('AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC PR VI GU AS MP'.split())
REQUIRED = {'institution_id','name','bureau','email','state','license_status','last_verified'}

def sample():
    rows = []
    bureaus = ['Community Banking','Mortgage Banking','Foreign Banking','Licensed Services','Banking Operations']
    for i in range(1, 251):
        rows.append(dict(institution_id=f'SYN{i:04}', name=f'Fictional Institution {i}',
            bureau=bureaus[(i-1)%5], email=f'contact{i}@example.org', state=['NY','NJ','CT','PA'][i%4],
            license_status='Active', last_verified='2026-09-01'))
    for i,r in enumerate(rows):
        if i%11 == 0: r['email'] = 'invalid-email'
        if i%17 == 0: r['name'] = ''
        if i%23 == 0: r['last_verified'] = '2025-01-01'
        if i%29 == 0: r['state'] = 'XX'
        if i%37 == 0: r['license_status'] = 'Unknown'
    rows[19]['institution_id'] = rows[18]['institution_id']
    return pd.DataFrame(rows)

def evaluate(frame, as_of=AS_OF):
    missing = REQUIRED-set(frame.columns)
    if missing: raise ValueError(f'Missing columns: {sorted(missing)}')
    if frame.empty: raise ValueError('Input has no records')
    df = frame.fillna('').astype(str).apply(lambda c:c.str.strip())
    counts = Counter(df.institution_id)
    exceptions, records = [], []
    for index,r in df.iterrows():
        try:
            age = (as_of-date.fromisoformat(r.last_verified)).days
            fresh = 0 <= age <= 90
        except ValueError: fresh = False
        checks = dict(required_name=bool(r['name']),
            valid_email=bool(re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',r.email)),
            valid_state=r.state in STATES, valid_status=r.license_status in {'Active','Surrendered','Suspended'},
            unique_id=counts[r.institution_id] == 1, fresh_record=fresh, valid_id=bool(r.institution_id))
        failed = [k for k,v in checks.items() if not v]
        for rule in failed:
            dim,weight,action = RULES[rule]
            exceptions.append(dict(row_number=len(records)+1,institution_id=r.institution_id,
                bureau=r.bureau,rule=rule,dimension=dim,severity=weight,action=action))
        weight_failed = sum(RULES[k][1] for k in failed)
        records.append(dict(row_number=len(records)+1,**r.to_dict(), failures=len(failed),
            quality_score=round(100*(1-weight_failed/sum(x[1] for x in RULES.values())),2)))
    results = pd.DataFrame(records)
    exc = pd.DataFrame(exceptions,columns=['row_number','institution_id','bureau','rule','dimension','severity','action'])
    summary = dict(data_type='Synthetic demonstration',as_of=str(as_of),records=len(df),
        failed_records=int((results.failures>0).sum()),exceptions=len(exc),
        rule_checks=len(df)*len(RULES),pass_rate=round(100*(1-len(exc)/(len(df)*len(RULES))),2),
        weighted_quality_score=round(float(results.quality_score.mean()),2),
        by_rule={k:int((exc.rule==k).sum()) for k in RULES},
        by_bureau=results.groupby('bureau').agg(records=('row_number','size'),
            score=('quality_score','mean')).round(2).reset_index().to_dict('records'))
    return results,exc,summary

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path)
    p.add_argument('--as-of',type=date.fromisoformat,default=AS_OF)
    a=p.parse_args()
    frame=pd.read_csv(a.input,dtype=str,keep_default_na=False) if a.input else sample()
    output=ROOT/'outputs'; output.mkdir(exist_ok=True)
    records,exceptions,summary=evaluate(frame,a.as_of)
    if a.input: summary['data_type']='User-supplied input; verify provenance'
    else:
        (ROOT/'data').mkdir(exist_ok=True);frame.to_csv(ROOT/'data/institutions.csv',index=False)
    records.to_csv(output/'scored_records.csv',index=False)
    exceptions.to_csv(output/'exceptions.csv',index=False)
    (output/'summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))

if __name__=='__main__': main()
