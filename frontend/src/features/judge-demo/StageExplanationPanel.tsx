import {ArrowRight,Box,Cloud,ExternalLink,FileCheck2,Fingerprint,ShieldCheck,Timer,Waypoints} from 'lucide-react';
import type {StageFact,StageView} from './types';
import StatusBadge from './StatusBadge';

const FactGrid=({title,items}:{title:string;items:StageFact[]})=><section className="jd-fact-section"><h3>{title}</h3><div className="jd-facts">{items.length?items.map((item,index)=><div className={`jd-fact ${item.emphasis??''}`} key={`${item.label}-${index}`}><small>{item.label}</small><strong>{item.value}</strong></div>):<p className="jd-empty">NOT_YET_EXECUTED</p>}</div></section>;

export default function StageExplanationPanel({stage}:{stage:StageView}){
 const scenarioProgress=stage.id==='simulation'?Math.min(100,((stage.scenarios?.length??0)/12)*100):0;
 return <article id="judge-stage-panel" className="jd-panel" role="tabpanel" aria-labelledby={`stage-tab-${stage.id}`} tabIndex={-1} aria-live="polite">
  <header><div><small>STAGE {stage.number} OF 15</small><h2>{stage.title}</h2><p>{stage.summary}</p></div><StatusBadge status={stage.status}/></header>
  <div className="jd-why"><Waypoints aria-hidden="true"/><div><h3>Why this matters</h3><p>{stage.why}</p></div></div>
  {stage.id==='simulation'&&<div className="jd-scenario-progress" aria-label={`${stage.scenarios?.length??0} of 12 scenarios complete`}><span style={{width:`${scenarioProgress}%`}}/><b>{stage.scenarios?.length??0} / 12 deterministic scenarios</b></div>}
  {stage.candidates&&<section className="jd-candidates" aria-label="Intervention comparison">{stage.candidates.map(candidate=><article className={`${candidate.eligible?'eligible':'disqualified'} ${candidate.candidate_id==='fast'&&!candidate.eligible?'fast-failure':''}`} key={candidate.candidate_id}><header><b>{candidate.name}</b><strong>{candidate.score}</strong></header><p>{candidate.action}</p><div><span>Risk {candidate.risk_score}/100</span><span>INR {candidate.cost_estimate_inr.toLocaleString('en-IN')}</span><span>{candidate.recovery_minutes} min</span></div><em>{candidate.eligible?'ELIGIBLE':`DISQUALIFIED · ${candidate.gates.find(g=>!g.passed)?.gate??'MANDATORY GATE'}`}</em></article>)}</section>}
  <div className="jd-data-grid"><FactGrid title="Inputs" items={stage.inputs}/><FactGrid title="Outputs" items={stage.outputs}/></div>
  <section className="jd-evidence"><h3><FileCheck2 aria-hidden="true"/> Evidence and provenance</h3><div className="jd-provenance"><span><Fingerprint/><small>Result hash</small><b>{stage.resultHash}</b></span><span><Waypoints/><small>Trace ID</small><b>{stage.traceId}</b></span><span><Timer/><small>Latency</small><b>{stage.latency}</b></span><span><Box/><small>Evidence IDs</small><b>{stage.evidenceIds.length?stage.evidenceIds.join(', '):'NOT_YET_EXECUTED'}</b></span></div></section>
  <div className="jd-boundaries"><section><ShieldCheck/><div><h3>Safety rule</h3><p>{stage.safetyRule}</p></div></section><section><Cloud/><div><h3>Google Cloud service</h3><p>{stage.googleService}</p><StatusBadge status={stage.fallbackState}/></div></section></div>
  <footer><div><small>JUDGE TAKEAWAY</small><p>{stage.takeaway}</p></div><div><small>NEXT STAGE</small><b>{stage.nextStage.toUpperCase()}</b>{stage.href&&<a href={stage.href}>Open operational stage <ExternalLink/></a>}</div></footer>
  <div className="jd-panel-boundary"><ShieldCheck/> PRODUCTION ACTION: NOT EXECUTED <ArrowRight aria-hidden="true"/> HUMAN AUTHORITY PRESERVED</div>
 </article>;
}
