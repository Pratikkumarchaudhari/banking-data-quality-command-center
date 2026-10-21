(function(root){
  'use strict';
  function filterExceptions(data,filters={}){
    const term=String(filters.search||'').trim().toLowerCase();
    return data.exceptions.filter(e=>(!filters.bureau||e.bureau===filters.bureau)
      &&(!filters.column||e.column===filters.column)
      &&(!filters.dimension||e.dimension===filters.dimension)
      &&(!filters.rule||e.rule===filters.rule)
      &&(!filters.weight||String(e.severity)===String(filters.weight))
      &&(!term||[e.institution_id,e.observed_value].some(v=>String(v).toLowerCase().includes(term))));
  }
  function recordOutcomes(data,rowNumber){
    const record=data.records.find(r=>Number(r.row_number)===Number(rowNumber));
    if(!record)return null;
    const failures=data.exceptions.filter(e=>Number(e.row_number)===Number(rowNumber));
    return {record,rules:data.summary.rule_catalog.map(r=>({...r,observed:record[r.column],
      outcome:failures.some(e=>e.rule===r.rule)?'Failed':'Passed'}))};
  }
  function csvCell(value){
    let text=String(value??'');
    // Guard spreadsheet formula interpretation when an exported value is untrusted.
    if(/^[=+\-@\t\r]/.test(text.trimStart()))text="'"+text;
    return '"'+text.replaceAll('"','""')+'"';
  }
  function exportCSV(rows){
    const fields=['row_number','institution_id','bureau','rule_id','rule','column','dimension','observed_value','expected','severity','action'];
    return [fields.map(csvCell).join(','),...rows.map(r=>fields.map(k=>csvCell(r[k])).join(','))].join('\r\n');
  }
  const api={filterExceptions,recordOutcomes,exportCSV};
  if(typeof module!=='undefined'&&module.exports){module.exports=api;return;}
  root.DQDashboard=api;
  const data=JSON.parse(document.getElementById('dq-data').textContent),s=data.summary;
  const byId=id=>document.getElementById(id);
  const fmt=n=>Number(n).toLocaleString(undefined,{maximumFractionDigits:2});
  function el(tag,cls,text){const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e;}
  function cell(tr,text,cls){const td=el('td',cls,text);tr.append(td);return td;}
  function badge(status){return el('span',status==='Failed'?'failed':status==='Passed'?'passed':'context',status);}
  byId('data-type').textContent=s.data_type;
  byId('as-of').textContent='Evaluation date: '+s.as_of;
  const metrics=[
    [s.records,'Input records',s.passed_records+' pass all rules'],
    [s.input_columns,'Input columns',s.evaluated_columns+' evaluated · '+(s.input_columns-s.evaluated_columns)+' context only'],
    [s.rules_total,'Defined rules',s.rules_failed+' with violations · '+s.rules_passed+' fully pass'],
    [s.rule_checks,'Evaluated checks',s.passed_checks+' passed checks'],
    [s.exceptions,'Failed checks',s.failed_records+' distinct records affected'],
    [s.pass_rate+'%','Check pass rate','Weighted quality score: '+s.weighted_quality_score+' / 100']
  ];
  metrics.forEach(([value,label,note])=>{const card=el('div','metric');card.append(el('strong','',typeof value==='number'?fmt(value):value),el('span','',label),el('small','',note));byId('metrics').append(card);});
  byId('reconciliation').textContent=`${fmt(s.rule_checks)} checks = ${fmt(s.passed_checks)} passed + ${fmt(s.exceptions)} failed. ${fmt(s.records)} records = ${fmt(s.passed_records)} with no failures + ${fmt(s.failed_records)} with one or more failures. A failed check is not the same as a failed record.`;
  byId('runtime').textContent='Python '+s.platform.python+' · Pandas '+s.platform.pandas+' · Policy '+s.platform.policy_version;
  byId('provenance').textContent='Source: '+(s.source_name||'deterministic synthetic sample')+' · Normalized dataset SHA-256: '+s.platform.dataset_fingerprint.slice(0,16)+'… · Input fields are normalized to strings; schema presence is checked before evaluation.';
  s.dimension_results.forEach(d=>{const card=el('div','dimension');card.append(el('h3','',d.dimension),el('strong','',fmt(d.failed)),el('p','','failed of '+fmt(d.checked)+' checks · '+d.pass_rate+'% pass'));const track=el('div','track'),fill=el('div','fill');fill.style.width=d.pass_rate+'%';track.append(fill);card.append(track,el('p','',d.affected_records+' affected records · '+d.rules+' rule'+(d.rules===1?'':'s')));byId('dimension-grid').append(card);});
  s.rule_catalog.forEach(r=>{
    const tr=el('tr');const name=cell(tr,r.rule_id+' · '+r.title);
    const details=el('details','logic');details.append(el('summary','','Inspect logic & platform'),el('p','',r.expected),el('pre','',r.logic),el('p','',r.platform+' · '+r.implementation),el('p','','Next action: '+r.action));name.append(details);
    cell(tr,r.column);cell(tr,r.dimension);cell(tr,r.weight);cell(tr,fmt(r.checked));cell(tr,fmt(r.passed));
    const failureCell=cell(tr,'');const button=el('button','text-button',fmt(r.failed));button.type='button';button.disabled=!r.failed;button.setAttribute('aria-label','Inspect '+r.failed+' failures for '+r.rule_id);
    button.addEventListener('click',()=>{resetFilters();byId('filter-rule').value=r.rule;renderQueue();byId('exceptions').scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});});failureCell.append(button);
    cell(tr,r.pass_rate+'%');cell(tr,'').append(badge(r.status));byId('rule-table').append(tr);
  });
  s.column_profiles.forEach(c=>{const tr=el('tr');cell(tr,c.column);cell(tr,c.missing);cell(tr,c.distinct);cell(tr,c.rules.join(', ')||'—');cell(tr,fmt(c.rule_checks));cell(tr,fmt(c.failed_checks));cell(tr,c.affected_records);cell(tr,c.pass_rate===null?'—':c.pass_rate+'%');cell(tr,'').append(badge(c.rules.length?'Evaluated':'Not assessed'));byId('column-table').append(tr);});
  function options(id,items,label){const select=byId(id);const all=el('option','',label);all.value='';select.append(all);items.forEach(item=>{const o=el('option','',typeof item==='string'?item:item.label);o.value=typeof item==='string'?item:item.value;select.append(o);});}
  options('filter-bureau',[...new Set(data.records.map(r=>r.bureau))].sort(),'All bureaus');
  options('filter-column',s.column_profiles.map(c=>c.column),'All columns');
  options('filter-dimension',s.dimension_results.map(d=>d.dimension),'All dimensions');
  options('filter-rule',s.rule_catalog.map(r=>({value:r.rule,label:r.rule_id+' · '+r.rule})),'All rules');
  options('filter-weight',[...new Set(s.rule_catalog.map(r=>String(r.weight)))].sort(),'All weights');
  function filters(){return {bureau:byId('filter-bureau').value,column:byId('filter-column').value,dimension:byId('filter-dimension').value,rule:byId('filter-rule').value,weight:byId('filter-weight').value,search:byId('filter-search').value};}
  function resetFilters(){['bureau','column','dimension','rule','weight','search'].forEach(k=>byId('filter-'+k).value='');}
  function renderQueue(){
    const rows=filterExceptions(data,filters()),tbody=byId('exception-table');tbody.replaceChildren();
    byId('queue-status').textContent=rows.length+' of '+s.exceptions+' failed checks shown · '+new Set(rows.map(r=>r.row_number)).size+' distinct source rows';
    byId('export').disabled=!rows.length;
    if(!rows.length){const tr=el('tr'),td=cell(tr,'No failed checks match these filters.','empty');td.colSpan=10;tbody.append(tr);return;}
    rows.forEach(r=>{const tr=el('tr');cell(tr,r.row_number);cell(tr,r.institution_id||'(blank)');cell(tr,r.bureau);cell(tr,r.column);cell(tr,r.observed_value===''?'(blank)':r.observed_value,'observed');cell(tr,r.expected,'expected');cell(tr,r.rule_id);cell(tr,r.severity);cell(tr,r.action,'expected');const td=cell(tr,'');const button=el('button','text-button','Inspect row');button.type='button';button.setAttribute('aria-label','Inspect source row '+r.row_number);button.addEventListener('click',()=>showRecord(r.row_number));td.append(button);tbody.append(tr);});
  }
  function showRecord(rowNumber){
    const detail=recordOutcomes(data,rowNumber);if(!detail)return;
    byId('record-title').textContent='Source row '+rowNumber+' · '+(detail.record.institution_id||'(blank ID)');
    byId('record-score').textContent=detail.record.failures+' failed rules · Weighted score '+detail.record.quality_score+' / 100';
    const fields=byId('record-fields');fields.replaceChildren();s.column_profiles.forEach(c=>{const field=el('div','record-field');field.append(el('span','',c.column+(c.rules.length?'':' · context only')),el('strong','',detail.record[c.column]===''?'(blank)':detail.record[c.column]));fields.append(field);});
    const rules=byId('record-rules');rules.replaceChildren();detail.rules.forEach(r=>{const tr=el('tr');cell(tr,r.rule_id+' · '+r.title);cell(tr,r.column);cell(tr,r.observed===''?'(blank)':r.observed);cell(tr,'').append(badge(r.outcome));cell(tr,r.expected);rules.append(tr);});
    byId('record-dialog').showModal();
  }
  ['bureau','column','dimension','rule','weight'].forEach(k=>byId('filter-'+k).addEventListener('change',renderQueue));byId('filter-search').addEventListener('input',renderQueue);
  byId('reset').addEventListener('click',()=>{resetFilters();renderQueue();});
  byId('close-dialog').addEventListener('click',()=>byId('record-dialog').close());
  byId('export').addEventListener('click',()=>{const csv=exportCSV(filterExceptions(data,filters()));const url=URL.createObjectURL(new Blob(['\uFEFF'+csv],{type:'text/csv;charset=utf-8'}));const link=el('a');link.href=url;link.download='banking-quality-filtered-exceptions.csv';document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),0);});
  renderQueue();
})(typeof globalThis!=='undefined'?globalThis:this);
