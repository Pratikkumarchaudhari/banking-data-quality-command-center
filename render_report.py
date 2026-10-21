"""Render a standalone report from the evaluated records and rule outcomes."""
from pathlib import Path
import json
import pandas as pd

ROOT=Path(__file__).resolve().parent

def write_report(records,exceptions,summary):
    payload=dict(summary=summary,records=records.to_dict('records'),exceptions=exceptions.to_dict('records'))
    # A user value must never be able to close the embedded JSON script element.
    data=json.dumps(payload,ensure_ascii=False,allow_nan=False).replace('<','\\u003c')
    template=(ROOT/'report_template.html').read_text(encoding='utf-8')
    output=template.replace('__DQ_SCRIPT__',(ROOT/'dashboard.js').read_text(encoding='utf-8'),1).replace('__DQ_DATA__',data,1)
    (ROOT/'report.html').write_text(output,encoding='utf-8')
    return output

if __name__=='__main__':
    out=ROOT/'outputs'
    write_report(pd.read_csv(out/'scored_records.csv',keep_default_na=False),
        pd.read_csv(out/'exceptions.csv',keep_default_na=False),json.loads((out/'summary.json').read_text()))
