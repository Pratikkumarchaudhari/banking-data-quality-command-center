const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const api=require(path.join(root,'dashboard.js'));
const report=fs.readFileSync(path.join(root,'report.html'),'utf8');
const data=JSON.parse(report.match(/<script id="dq-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
test('All failures are visible and intersecting filters combine with AND',()=>{
 assert.equal(api.filterExceptions(data).length,67);
 const filtered=api.filterExceptions(data,{rule:'valid_email',bureau:'Community Banking'});
 assert.ok(filtered.length>0);
 assert.ok(filtered.every(r=>r.rule==='valid_email'&&r.bureau==='Community Banking'));
 assert.equal(api.filterExceptions(data,{column:'bureau'}).length,0);
});
test('Duplicate rows retain separate row-level evidence',()=>{
 const rows=api.filterExceptions(data,{rule:'unique_id'});
 assert.equal(rows.length,2);assert.equal(rows[0].institution_id,rows[1].institution_id);
 assert.notEqual(rows[0].row_number,rows[1].row_number);
 rows.forEach(r=>{const detail=api.recordOutcomes(data,r.row_number);assert.equal(detail.rules.length,7);assert.equal(detail.rules.find(x=>x.rule==='unique_id').outcome,'Failed');});
});
test('Observed-value search and record summary match the saved data',()=>{
 const rows=api.filterExceptions(data,{search:'invalid-email'});assert.equal(rows.length,23);
 const detail=api.recordOutcomes(data,rows[0].row_number);
 assert.equal(detail.rules.filter(r=>r.outcome==='Failed').length,detail.record.failures);
 assert.equal(api.recordOutcomes(data,-1),null);
});
test('CSV preserves quoting and neutralizes spreadsheet formulas',()=>{
 const csv=api.exportCSV([{row_number:1,institution_id:' =1+1',observed_value:'a,"b"'}]);
 assert.ok(csv.includes('"\' =1+1"'));
 assert.ok(csv.includes('"a,""b"""'));
 assert.equal(api.exportCSV([]).split('\r\n').length,1);
});
