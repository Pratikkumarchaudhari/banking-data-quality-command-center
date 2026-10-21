"""Deterministic banking-data quality rules and auditable exception output."""
import argparse
from collections import Counter
from datetime import date
from pathlib import Path
import json
import re
import sys
from hashlib import sha256
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
RULE_DETAILS = {
    'required_name': ('DQ001','name','Institution name is required','Trimmed name must be nonblank','bool(trimmed name)'),
    'valid_email': ('DQ002','email','Contact email has valid syntax','A nonblank email with no whitespace and a dotted domain','Regex: [^\\s@]+@[^\\s@]+\\.[^\\s@]+'),
    'valid_state': ('DQ003','state','Jurisdiction code is supported','One of the configured two-letter US state/territory codes','state in STATES; case-sensitive'),
    'valid_status': ('DQ004','license_status','License status is recognized','Active, Surrendered, or Suspended','status in {Active, Surrendered, Suspended}'),
    'unique_id': ('DQ005','institution_id','Institution identifier is unique','Identifier occurs exactly once in this input','count(institution_id) == 1; flag every duplicate row'),
    'fresh_record': ('DQ006','last_verified','Record was verified within 90 days','Valid ISO date with age from 0 through 90 days as of the evaluation date','0 <= (as_of - parsed_date).days <= 90'),
    'valid_id': ('DQ007','institution_id','Institution identifier is present','Trimmed identifier must be nonblank','bool(trimmed institution_id)'),
}

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
            rule_id,column,title,expected,logic = RULE_DETAILS[rule]
            exceptions.append(dict(row_number=len(records)+1,institution_id=r.institution_id,
                bureau=r.bureau,rule=rule,dimension=dim,severity=weight,action=action,
                rule_id=rule_id,column=column,observed_value=r[column],expected=expected))
        weight_failed = sum(RULES[k][1] for k in failed)
        records.append(dict(row_number=len(records)+1,**r.to_dict(), failures=len(failed),
            quality_score=round(100*(1-weight_failed/sum(x[1] for x in RULES.values())),2)))
    results = pd.DataFrame(records)
    exc = pd.DataFrame(exceptions,columns=['row_number','institution_id','bureau','rule','dimension','severity','action',
        'rule_id','column','observed_value','expected'])
    rule_catalog=[]
    for key,(dimension,weight,action) in RULES.items():
        rule_id,column,title,expected,logic=RULE_DETAILS[key]
        failures=int((exc.rule==key).sum())
        rule_catalog.append(dict(rule=key,rule_id=rule_id,column=column,title=title,expected=expected,logic=logic,
            dimension=dimension,weight=weight,action=action,checked=len(df),failed=failures,passed=len(df)-failures,
            pass_rate=round(100*(1-failures/len(df)),2),status='Failed' if failures else 'Passed',
            platform='Python / Pandas',implementation='pipeline.py:evaluate'))
    column_profiles=[]
    for column in df.columns:
        applicable=[r for r in rule_catalog if r['column']==column]
        column_exc=exc[exc.column==column]
        checked=len(df)*len(applicable)
        column_profiles.append(dict(column=column,input_type='String (normalized)',
            missing=int(df[column].eq('').sum()),distinct=int(df[column].nunique()),
            rules=[r['rule_id'] for r in applicable],rule_checks=checked,failed_checks=len(column_exc),
            affected_records=int(column_exc.row_number.nunique()),
            pass_rate=round(100*(1-len(column_exc)/checked),2) if checked else None,
            coverage='Evaluated' if applicable else 'Context only — not evaluated'))
    dimension_results=[]
    for dimension in dict.fromkeys(r['dimension'] for r in rule_catalog):
        dim_rules=[r for r in rule_catalog if r['dimension']==dimension]
        dim_exc=exc[exc.dimension==dimension];checked=sum(r['checked'] for r in dim_rules)
        dimension_results.append(dict(dimension=dimension,rules=len(dim_rules),checked=checked,
            failed=len(dim_exc),passed=checked-len(dim_exc),affected_records=int(dim_exc.row_number.nunique()),
            pass_rate=round(100*(1-len(dim_exc)/checked),2)))
    summary = dict(data_type='Synthetic demonstration',as_of=str(as_of),records=len(df),
        failed_records=int((results.failures>0).sum()),exceptions=len(exc),
        rule_checks=len(df)*len(RULES),pass_rate=round(100*(1-len(exc)/(len(df)*len(RULES))),2),
        weighted_quality_score=round(float(results.quality_score.mean()),2),
        by_rule={k:int((exc.rule==k).sum()) for k in RULES},
        by_bureau=results.groupby('bureau').agg(records=('row_number','size'),
            score=('quality_score','mean')).round(2).reset_index().to_dict('records'),
        passed_records=int((results.failures==0).sum()),passed_checks=len(df)*len(RULES)-len(exc),
        input_columns=len(df.columns),evaluated_columns=sum(bool(c['rules']) for c in column_profiles),
        rules_total=len(RULES),rules_failed=sum(r['status']=='Failed' for r in rule_catalog),
        rules_passed=sum(r['status']=='Passed' for r in rule_catalog),
        rule_catalog=rule_catalog,column_profiles=column_profiles,dimension_results=dimension_results,
        platform=dict(rule_authoring='Python rule definitions in pipeline.py',rule_execution='Python / Pandas batch evaluation',
            reporting='HTML / CSS / JavaScript',source_format='CSV or deterministic in-memory sample',
            python=sys.version.split()[0],pandas=pd.__version__,policy_version='1.1',
            dataset_fingerprint=sha256(df.to_csv(index=False).encode()).hexdigest(),
            sql_role='SQLite-compatible reference queries; not the dashboard execution engine',
            deployment='Static sample dashboard; no connection to live bank or employer systems'))
    return results,exc,summary

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path)
    p.add_argument('--as-of',type=date.fromisoformat,default=AS_OF)
    a=p.parse_args()
    frame=pd.read_csv(a.input,dtype=str,keep_default_na=False) if a.input else sample()
    output=ROOT/'outputs'; output.mkdir(exist_ok=True)
    records,exceptions,summary=evaluate(frame,a.as_of)
    summary['source_name']=a.input.name if a.input else 'data/institutions.csv (generated synthetic sample)'
    if a.input: summary['data_type']='User-supplied input; verify provenance'
    else:
        (ROOT/'data').mkdir(exist_ok=True);frame.to_csv(ROOT/'data/institutions.csv',index=False)
    records.to_csv(output/'scored_records.csv',index=False)
    exceptions.to_csv(output/'exceptions.csv',index=False)
    (output/'summary.json').write_text(json.dumps(summary,indent=2))
    from render_report import write_report
    write_report(records,exceptions,summary)
    print(json.dumps(summary,indent=2))

if __name__=='__main__': main()
