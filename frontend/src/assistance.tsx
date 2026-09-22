import {useEffect, useState} from 'react';
import {Sparkles, Loader2, AlertTriangle} from 'lucide-react';
import './assistance.css';

type Row = Record<string, any>;
type Api = (path:string, body?:unknown)=>Promise<any>;

export function EvidenceAssessment({candidate, inspect}:{candidate:Row;inspect:(id:string)=>void}) {
  const a=candidate.evidence_assessment;
  if(!a)return null;
  return <section className="ai-assessment" aria-label="AI evidence assessment">
    <div className="ai-assessment-heading"><Sparkles size={17}/><strong>Evidence assessment</strong><span className={'evidence-level '+a.strength}>{a.strength} evidence</span></div>
    <div className="assessment-rubric">{[['Symptom match',a.symptom_match],['Context match',a.context_match],['Resolution support',a.resolution_support]].map(([label,value])=><div key={label}><small>{label}</small><strong>{value}</strong></div>)}</div>
    <p>{a.rationale}</p>
    {a.contradictions.length>0&&<div className="ai-caution"><strong>Conflicting evidence</strong><ul>{a.contradictions.map((s:string,i:number)=><li key={i}>{s}</li>)}</ul></div>}
    {a.missing_context.length>0&&<div><strong>Still to confirm</strong><ul>{a.missing_context.map((s:string,i:number)=><li key={i}>{s}</li>)}</ul></div>}
    <div className="button-row">{a.source_ids.map((id:string)=><button key={id} className="text-button" onClick={()=>inspect(id.split('@')[0])}>{id}</button>)}</div>
    <small>AI relevance judgment, not a success probability. Applicability: {candidate.assessment.status.replaceAll('_',' ')}. Compatibility restrictions remain authoritative.</small>
  </section>;
}

export function CaptureAssistant({api,form,setForm,disabled,onBusy}:{api:Api;form:Row;setForm:(form:Row)=>void;disabled:boolean;onBusy:(value:boolean)=>void}) {
  const [busy,setBusy]=useState(false),[error,setError]=useState('');
  async function generate(){
    setBusy(true);onBusy(true);setError('');
    try{
      const record=await api(`/gaps/${form.gap_id}/suggest-resolution`,{notes:form.notes});
      const r=record.result;
      setForm({...form,title:r.title,steps:r.steps.join('\n'),validation:r.validation,
        symptoms:r.symptoms.join('\n'),prerequisites:r.prerequisites.join('\n'),limitations:r.limitations.join('\n'),
        missing_information:r.missing_information,assistance_id:record.id,human_reviewed:false,notes_changed:false});
    }catch(e){setError((e as Error).message);}finally{setBusy(false);onBusy(false);}
  }
  return <div className="ai-assessment">
    <div className="ai-assessment-heading"><Sparkles size={17}/><strong>Draft from troubleshooting notes</strong></div>
    <p>Paste what was observed, the actions actually performed and how recovery was checked. Gemini extracts a draft for you to edit; it cannot publish it.</p>
    <label className="field">Consultant notes<textarea rows={5} maxLength={12000} disabled={busy||disabled} value={form.notes||''} onChange={e=>setForm({...form,notes:e.target.value,human_reviewed:false,notes_changed:!!form.assistance_id})} placeholder="Observed… We performed… Recovery was verified by…"/></label>
    <button type="button" className="button secondary" disabled={busy||disabled||(form.notes||'').trim().length<30} onClick={generate}>{busy?<Loader2 size={16} className="spin"/>:<Sparkles size={16}/>} {busy?'Preparing draft…':'Prepare AI draft'}</button>
    {error&&<p className="ai-caution" role="alert">{error}</p>}
    {form.notes_changed&&<p className="ai-caution">Notes changed. Prepare the draft again before capturing so its provenance matches your notes.</p>}
    {form.assistance_id&&<><p className="ai-caution">Unapproved AI draft. Review the editable fields below before capturing.</p>{form.missing_information?.length>0&&<><strong>Missing information to resolve</strong><ul>{form.missing_information.map((s:string,i:number)=><li key={i}>{s}</li>)}</ul></>}
    {['symptoms','prerequisites','limitations'].map(key=><label className="field" key={key}>{key[0].toUpperCase()+key.slice(1)} — one per line<textarea rows={2} value={form[key]||''} maxLength={8000} onChange={e=>setForm({...form,[key]:e.target.value,human_reviewed:false})}/></label>)}
    <label className="ai-review-check"><input type="checkbox" disabled={!!form.notes_changed} checked={!!form.human_reviewed} onChange={e=>setForm({...form,human_reviewed:e.target.checked})}/>I have checked the draft against the actual resolution and addressed missing information. It still requires publication review.</label></>}
  </div>;
}

export function AssistancePanel({api,kind,target='',revision,onIncident}:{api:Api;kind:'impact'|'clusters';target?:string;revision:string;onIncident?:(id:string)=>void}) {
  const [record,setRecord]=useState<Row|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
  useEffect(()=>{let active=true;api(`/assistance/${kind}?target=${encodeURIComponent(target)}`).then(r=>{if(active){setRecord(r);setError('');}}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[kind,target,revision]);
  async function generate(){setBusy(true);setError('');try{setRecord(await api(kind==='impact'?`/changes/${target}/assess-impact`:'/gaps/cluster',{}));}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
  const impact=kind==='impact';
  return <section className="ai-assessment">
    <div className="ai-assessment-heading"><Sparkles size={17}/><strong>{impact?'AI change-impact review':'Recurring knowledge gaps'}</strong></div>
    <p>{impact?'Identify procedures that may need expert attention, with quotations from the change and procedure.':'Group similar unresolved incidents and prioritize by frequency. Individual gaps and ownership remain intact.'}</p>
    <button className="button secondary" disabled={busy} onClick={generate}>{busy?<Loader2 size={16} className="spin"/>:<Sparkles size={16}/>} {busy?'Assessing…':record?'Refresh assessment':impact?'Assess potential impact':'Group unresolved gaps'}</button>
    {error&&<p className="ai-caution" role="alert">{error}</p>}
    {record&&<><small className="ai-record-meta">{record.model} · {new Date(record.created_at).toLocaleString()} · {record.cached?'Reused cached assessment':'Saved assessment'}</small>
    {record.stale&&<p className="ai-caution" role="alert"><AlertTriangle size={15}/> Context changed. This assessment is stale; refresh before using it.</p>}
    {impact?<>
      {record.result.affected.length===0&&<p>No supported impact relationship was identified. This is not a declaration that procedures are safe.</p>}
      {record.result.affected.map((item:Row)=><article className="ai-result-item" key={item.passport_id}><strong>{item.passport_id}</strong><span className="evidence-level moderate">Expert review required</span><p>{item.reason}</p>{item.references.map((r:Row,i:number)=><details key={i}><summary>{r.source_id}</summary><blockquote>{r.quote}</blockquote></details>)}</article>)}
      {record.result.uncertainties.length>0&&<><strong>Uncertainties</strong><ul>{record.result.uncertainties.map((s:string,i:number)=><li key={i}>{s}</li>)}</ul></>}
    </>:<><p>{record.result.coverage} unresolved gaps assessed · suggested groups, not confirmed shared causes</p>{record.result.groups.map((group:Row,i:number)=><article className="ai-result-item" key={i}><div className="ai-assessment-heading"><strong>{group.title}</strong><span className="evidence-level">{group.frequency} incident{group.frequency===1?'':'s'}</span></div><p>{group.rationale}</p><small>Systems: {group.systems.join(', ')}</small><div className="button-row">{group.incident_ids.map((id:string)=><button className="text-button" key={id} onClick={()=>onIncident?.(id)}>{id}</button>)}</div></article>)}</>}
    </>}
  </section>;
}
