import {ArrowRight,ExternalLink,ShieldCheck,Waypoints} from 'lucide-react';
import type {JudgeDemoStage,StageFact} from './types';
import StatusBadge from './StatusBadge';

const List=({title,items}:{title:string;items:string[]})=><section className="jd-ordered-section"><h3>{title}</h3>{items.length?<ul>{items.map((item,index)=><li key={`${item}-${index}`}>{item}</li>)}</ul>:<p>No additional backend evidence is available for this field.</p>}</section>;
const Facts=({items}:{items:StageFact[]})=><div className="jd-facts">{items.length?items.map((item,index)=><div className={`jd-fact ${item.emphasis??''}`} key={`${item.label}-${index}`}><small>{item.label}</small><strong>{item.value}</strong></div>):<p className="jd-empty">NOT_YET_EXECUTED</p>}</div>;

export default function StageExplanationPanel({stage}:{stage:JudgeDemoStage}){
 return <article id="judge-stage-panel" className="jd-panel" role="tabpanel" aria-labelledby={`stage-tab-${stage.id}`} tabIndex={-1} aria-live="polite">
  <header><div><small>STAGE {stage.order} OF 20</small><h2>{stage.title}</h2><p>{stage.shortDescription}</p></div>{stage.metric&&<strong className="jd-metric">{stage.metric}</strong>}</header>
  <section className="jd-purpose"><Waypoints/><div><h3>1. Purpose</h3><p>{stage.purpose}</p></div></section>
  <section className="jd-ordered-section"><h3>2. What it does</h3><p>{stage.whatItDoes}</p></section>
  <section className="jd-ordered-section"><h3>3. Why it matters in SentinelOps Nexus</h3><p>{stage.whyItMatters}</p></section>
  <List title="4. What is already implemented" items={stage.implemented}/>
  <List title="5. What is still missing for live operation" items={stage.missingForLiveOperation}/>
  <section className="jd-evidence-status"><div><h3>6. Current evidence status</h3><p>Status follows the architectural explanation and reflects only available backend or authenticated runtime evidence.</p></div><StatusBadge status={stage.status}/></section>
  <section className="jd-ordered-section"><h3>7. Live backend data</h3><Facts items={stage.liveData}/>{stage.candidates&&<div className="jd-candidates">{stage.candidates.map(c=><article className={`${c.eligible?'eligible':'disqualified'} ${c.candidate_id==='fast'&&!c.eligible?'fast-failure':''}`} key={c.candidate_id}><header><b>{c.name}</b><strong>{c.score}</strong></header><p>{c.action}</p><em>{c.eligible?'ELIGIBLE':`DISQUALIFIED · ${c.gates.find(g=>!g.passed)?.gate??'MANDATORY GATE'}`}</em></article>)}</div>}</section>
  <List title="8. Evidence references" items={stage.evidenceReferences}/><List title="9. Hashes" items={stage.hashes}/><List title="10. Timings" items={stage.timings}/><List title="11. Assumptions" items={stage.assumptions}/><List title="12. Safety implications" items={stage.safetyImplications}/><List title="13. Google Cloud service involved" items={stage.googleCloudServices}/>
  <section className="jd-next"><div><h3>14. Next stage</h3><b>{stage.nextStageId?.replaceAll('-',' ').toUpperCase()??'COMPLETE'}</b>{stage.href&&<a href={stage.href}>Open operational stage <ExternalLink/></a>}</div><div><h3>15. Judge takeaway</h3><p>{stage.judgeTakeaway}</p></div></section>
  <div className="jd-panel-boundary"><ShieldCheck/> PRODUCTION ACTION: NOT EXECUTED <ArrowRight/> HUMAN AUTHORITY PRESERVED</div>
 </article>;
}
