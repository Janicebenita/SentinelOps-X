import {useEffect,useState,type ReactNode} from 'react';
import {useMutation,useQuery,useQueryClient} from '@tanstack/react-query';
import {Activity,CheckCircle2,ChevronLeft,ChevronRight,Pause,Play,RotateCcw,ShieldCheck} from 'lucide-react';
import {nexusApi} from '../api/client';
import type {NexusRun} from '../types';

const label=(value:unknown)=>String(value??'NOT AVAILABLE').replaceAll('_',' ');
const yes=(value:unknown)=>value?<span className="demo-pass">YES</span>:<span className="demo-warn">NO</span>;

type DemoStep={title:string;summary:string;explanation:string;value:ReactNode;ready:boolean;href?:string};

export default function JudgeDemoPage(){
 const cache=useQueryClient();
 const [activeStep,setActiveStep]=useState(0);
 const [playing,setPlaying]=useState(false);
 const workflows=useQuery({queryKey:['judge-workflows'],queryFn:nexusApi.workflows});
 const run=workflows.data?.at(-1) as NexusRun|undefined;
 const integrations=useQuery({queryKey:['judge-integrations'],queryFn:nexusApi.integrations});
 const antigravity=useQuery({queryKey:['judge-antigravity'],queryFn:nexusApi.antigravity});
 const a2a=useQuery({queryKey:['judge-a2a',run?.id],queryFn:()=>nexusApi.a2a(run!.id),enabled:!!run});
 const audit=useQuery({queryKey:['judge-audit',run?.id],queryFn:()=>nexusApi.timeline(run!.id),enabled:!!run});
 const refresh=()=>Promise.all([
  cache.invalidateQueries({queryKey:['judge-workflows']}),
  cache.invalidateQueries({queryKey:['judge-integrations']}),
  cache.invalidateQueries({queryKey:['judge-a2a']}),
  cache.invalidateQueries({queryKey:['judge-audit']})
 ]);
 const seed=useMutation({mutationFn:nexusApi.seed,onSuccess:async()=>{await refresh();setActiveStep(0);setPlaying(false)}});
 const execute=useMutation({mutationFn:()=>nexusApi.runAll(run!.id),onSuccess:async()=>{await refresh();setActiveStep(0);setPlaying(true)}});
 const tournament=run?.tournament_json;
 const candidates=tournament?.candidates??[];
 const recommended=candidates.find(x=>x.candidate_id===tournament?.recommended_candidate_id);
 const fast=candidates.find(x=>x.candidate_id==='fast');
 const forecast=run?.forecast_json??{};
 const impact=run?.impact_json??{};
 const modelRows=integrations.data??[];
 const integration=(name:string)=>modelRows.find(x=>x.integration.toLowerCase().includes(name));
 const busy=seed.isPending||execute.isPending;
 const approvalHref=run?`/workflows/${run.id}/approval`:'/command-centre';
 const cloudRuntime=location.hostname.endsWith('.run.app');
 const steps:DemoStep[]=[
  {title:'1. Problem',summary:'Reactive monitoring arrives too late.',explanation:'The operator begins with a concrete business problem: Redis pressure is rising on the Payment Service critical path while the conventional alert still appears healthy.',value:<b>{label(run?.name)}</b>,ready:!!run},
  {title:'2. Current healthy state',summary:'The alert has not fired yet.',explanation:'Persisted seeded telemetry starts below the reactive threshold. This establishes why prediction provides earlier decision time than alert-only operations.',value:<b>{run?'VERIFIED BASELINE':'START WORKFLOW'}</b>,ready:!!run},
  {title:'3. Rising Redis pressure',summary:'A bounded trend is calculated.',explanation:'The backend fits the documented deterministic linear model to visible Redis measurements. This equation is evidence, not an LLM-generated forecast.',value:<b>{label(forecast.equation)}</b>,ready:forecast.equation!=null},
  {title:'4. Safe capacity crossing',summary:'The intervention window becomes visible.',explanation:'The authoritative forecast calculates when the safe-capacity threshold is crossed. In the canonical seed, operators receive a thirty-minute warning.',value:<b>+{label(forecast.predicted_crossing_minutes)} minutes</b>,ready:forecast.predicted_crossing_minutes!=null},
  {title:'5. Customer-impact estimate',summary:'Technical risk is translated into exposure.',explanation:'The business-impact service applies visible traffic, conversion, and order-value assumptions. The amount is an operational estimate, never guaranteed revenue.',value:<b>+{label(forecast.predicted_customer_impact_minutes)} min · INR {Number(impact.revenue_exposure_inr??0).toLocaleString()}</b>,ready:forecast.predicted_customer_impact_minutes!=null},
  {title:'6. Digital Twin',summary:'The experiment is bounded and reproducible.',explanation:'A version-locked Twin manifest records the fixed seed, inputs, network policy, and content hash so every scenario can be replayed under the same assumptions.',value:<b>{String(run?.twin_json?.manifest_hash??'NOT AVAILABLE').slice(0,16)}</b>,ready:!!run?.twin_json?.manifest_hash},
  {title:'7. Scenario progress',summary:'Twelve counterfactual futures are replayed.',explanation:'The Simulation Agent persists each deterministic baseline, stress, and failure scenario. The UI reports backend results rather than incrementing a cosmetic counter.',value:<b>{run?.scenarios_json?.length??0} / 12 complete</b>,ready:(run?.scenarios_json?.length??0)===12},
  {title:'8. Intervention tournament',summary:'FAST, SAFE, and OPTIMAL compete.',explanation:'The Optimization Agent compares recovery, residual risk, reversibility, cost, and mandatory gates. Score alone can never rescue an ineligible candidate.',value:<b>{candidates.map(x=>`${x.candidate_id.toUpperCase()}: ${x.score}`).join(' · ')||'PENDING'}</b>,ready:candidates.length>0},
  {title:'9. FAST disqualification',summary:'A plausible false fix is rejected.',explanation:'FAST improves application capacity but fails mandatory failover safety. Deterministic eligibility overrides its score, demonstrating why the tournament is safety-first.',value:<b>{fast?yes(!fast.eligible):'NOT AVAILABLE'}</b>,ready:!!fast},
  {title:'10. Gemini reasoning',summary:'Evidence is synthesized with explicit fallback.',explanation:'Gemini explains contradictions, missing evidence, scenarios, and recommendations. It cannot calculate gates, approve, change state, or execute production actions.',value:<Status value={integration('gemini')?.status}/>,ready:!integrations.isLoading},
  {title:'11. Gemma policy review',summary:'A secondary advisory critique is applied.',explanation:'Gemma checks recommendation-to-gate consistency and evidence completeness. Its response is advisory and is structurally prevented from overriding deterministic policy.',value:<Status value={integration('gemma')?.status}/>,ready:!integrations.isLoading},
  {title:'12. Mandatory Safety Gates',summary:'Backend policy decides eligibility.',explanation:'Configuration, failover, performance, evidence, and audit gates are evaluated by deterministic services. Models can explain these results but cannot alter them.',value:<b>{recommended?recommended.gates.filter(g=>g.mandatory&&g.passed).length:'—'} mandatory gates passed</b>,ready:!!recommended},
  {title:'13. Verification result',summary:'Evidence completeness is checked.',explanation:'The Verification Agent validates replay, safety, policy, evidence, audit readiness, and the disabled production boundary. It verifies; it never approves.',value:<b>{run?.state==='AWAITING_HUMAN'||run?.state==='DECIDED'?'VERIFIED':'PENDING'}</b>,ready:run?.state==='AWAITING_HUMAN'||run?.state==='DECIDED'},
  {title:'14. Executive recommendation',summary:'The highest-scoring eligible option is explained.',explanation:'The executive brief joins deterministic results with evidence-grounded narrative. The recommendation remains advisory until an authorized human records a decision.',value:<b>{label(recommended?.candidate_id)}</b>,ready:!!recommended},
  {title:'15. Human boundary',summary:'Automation stops at AWAITING_HUMAN.',explanation:'No model, agent, or tool can cross this boundary. The backend requires role verification, candidate eligibility, complete gates, and a mandatory human rationale.',value:<b>{label(run?.state)}</b>,ready:run?.state==='AWAITING_HUMAN'||run?.state==='DECIDED',href:approvalHref},
  {title:'16. Intern rejection',summary:'Inspection permission is not approval authority.',explanation:'The demonstration Intern credential may inspect and simulate, but a direct approval attempt is rejected by authoritative backend RBAC with HTTP 403.',value:<b>VERIFY ROLE MANUALLY</b>,ready:!!run,href:approvalHref},
  {title:'17. Senior rationale',summary:'A qualified role still needs justification.',explanation:'A verified Senior Developer receives approval permission only for a short-lived token and must provide rationale before the backend accepts the decision.',value:<b>OPEN APPROVAL STAGE</b>,ready:!!run,href:approvalHref},
  {title:'18. Audit-chain update',summary:'Every governed event is hash-linked.',explanation:'The audit service persists actor, action, evidence, previous hash, and current SHA-256 hash. Verification detects later tampering without claiming certified immutability.',value:<b>{String(audit.data?.at(-1)?.event_hash??'PENDING').slice(0,16)}</b>,ready:(audit.data?.length??0)>0},
  {title:'19. Evidence ZIP',summary:'The decision package unlocks after governance.',explanation:'After a recorded human decision, the backend generates the Evidence ZIP and manifest.sha256. Downloading evidence never deploys or modifies infrastructure.',value:<b>{run?.state==='DECIDED'?'AVAILABLE FOR VERIFICATION':'LOCKED'}</b>,ready:run?.state==='DECIDED',href:run?`/workflows/${run.id}/export`:undefined},
  {title:'20. Google Cloud evidence',summary:'Runtime and integration boundaries stay explicit.',explanation:'Cloud Run hosts the product services. Managed BigQuery, Pub/Sub, model, ADK, and Antigravity claims retain their individual evidence status—deployment never upgrades an unverified integration.',value:<b>{cloudRuntime?`CLOUD RUN · ${location.hostname}`:'LOCAL RUNTIME'} · A2A {a2a.data?.length??0} · MCP {label(integration('mcp')?.status)} · Antigravity {antigravity.data?.status==='DOCUMENTATION_OR_ACCESS_BLOCKED'?'BLOCKED BY PARTICIPANT ACCESS':label(antigravity.data?.status)}</b>,ready:!integrations.isLoading}
 ];
 const current=steps[activeStep]??steps[0];

 useEffect(()=>{
  if(!playing)return;
  const timer=window.setInterval(()=>setActiveStep(step=>{
   if(step>=steps.length-1){setPlaying(false);return step}
   return step+1;
  }),4500);
  return()=>window.clearInterval(timer);
 },[playing,steps.length]);

 useEffect(()=>{
  if(!playing)return;
  const reduced=typeof matchMedia==='function'&&matchMedia('(prefers-reduced-motion: reduce)').matches;
  const card=document.getElementById(`demo-step-${activeStep}`);
  if(card&&typeof card.scrollIntoView==='function')card.scrollIntoView({behavior:reduced?'auto':'smooth',block:'center'});
 },[activeStep,playing]);

 const selectStep=(index:number)=>{setActiveStep(index);setPlaying(false)};
 const previous=()=>{setPlaying(false);setActiveStep(step=>Math.max(0,step-1))};
 const next=()=>{setPlaying(false);setActiveStep(step=>Math.min(steps.length-1,step+1))};
 const restart=()=>{setActiveStep(0);setPlaying(true)};

 return <div className="product-page judge-demo"><nav><a href="/"><b>SENTINELOPS NEXUS</b></a><a href="/command-centre">Command Centre</a><a href="/agents">AI Workforce</a></nav><main>
  <header className="judge-hero"><div><small>INTERACTIVE EVIDENCE WORKSPACE</small><h1>Judge Demo</h1><p>Run the real backend workflow, then play or click through the evidence. Every number comes from persisted calculations; motion only guides the explanation.</p></div><div className="demo-actions"><button className="primary" onClick={()=>seed.mutate()} disabled={busy}><Play/>{seed.isPending?'Creating…':'Create deterministic workflow'}</button><button className="primary" onClick={()=>execute.mutate()} disabled={!run||busy}><Activity/>{execute.isPending?'Running backend…':'Run backend workflow'}</button></div></header>
  {(workflows.isError||seed.isError||execute.isError)&&<p className="form-error">The backend workflow could not be loaded. Start the API and retry.</p>}
  <div className="demo-status"><b>Workflow {run?.id??'—'}</b><span>{label(run?.state??'NOT_STARTED')}</span><span>Seed {run?.seed??'—'}</span><span>{run?.production_action_executed?'UNSAFE':'PRODUCTION ACTION: NOT EXECUTED'}</span></div>

  <section className="demo-player" aria-label="Interactive guided evidence tour" aria-live="polite">
   <div className="tour-progress" aria-hidden="true"><span style={{width:`${((activeStep+1)/steps.length)*100}%`}}/></div>
   <div className="demo-narrative">
    <div><small>GUIDED EXPLANATION · STEP {activeStep+1} OF {steps.length}</small><h2>{current.title}</h2><h3>{current.summary}</h3><p>{current.explanation}</p>{current.href&&<a className="tour-link" href={current.href}>Open this operational stage <ChevronRight/></a>}</div>
    <div className={`tour-result ${current.ready?'ready':'pending'}`}><small>LIVE BACKEND OUTCOME</small>{current.value}<span>{current.ready?'EVIDENCE AVAILABLE':'AWAITING WORKFLOW EVIDENCE'}</span></div>
   </div>
   <div className="tour-controls"><button onClick={previous} disabled={activeStep===0} aria-label="Previous evidence step"><ChevronLeft/></button><button className="tour-play" onClick={()=>setPlaying(value=>!value)} aria-label={playing?'Pause guided walkthrough':'Play guided walkthrough'}>{playing?<Pause/>:<Play/>}<span>{playing?'Pause':'Play walkthrough'}</span></button><button onClick={next} disabled={activeStep===steps.length-1} aria-label="Next evidence step"><ChevronRight/></button><button onClick={restart} aria-label="Restart guided walkthrough"><RotateCcw/><span>Restart</span></button></div>
  </section>

  {!run&&<section className="demo-onboarding"><Activity/><div><h2>Begin with a real workflow</h2><p>Click <b>Create deterministic workflow</b>, then <b>Run backend workflow</b>. When execution completes, the guided walkthrough starts automatically.</p></div></section>}

  <section className="judge-grid" aria-label="Clickable evidence steps">
   {steps.map((step,index)=><button type="button" id={`demo-step-${index}`} className={`demo-card ${index===activeStep?'active':''} ${step.ready?'available':'pending'}`} onClick={()=>selectStep(index)} key={step.title} aria-current={index===activeStep?'step':undefined}>
    <span className="step-state"><i/>{step.ready?'AVAILABLE':'PENDING'}</span><h2>{step.title}</h2><p>{step.summary}</p><div>{step.value}</div><small>Click to explain</small>
   </button>)}
  </section>
  <section className="why-panel"><h2>Why this matters</h2><span>Customer impact surfaced: +{label(forecast.predicted_customer_impact_minutes)} min</span><span>Unsafe fix rejected: {fast&&!fast.eligible?'YES':'PENDING'}</span><span>Evidence generated: {audit.data?.length??0} audit events</span><span>Human authority preserved: YES</span></section>
  <div className="boundary"><ShieldCheck/> PRODUCTION ACTION: NOT EXECUTED</div>
 </main></div>
}

function Status({value}:{value?:string}){const raw=value??'REQUIRES_CREDENTIALS';const status=raw==='DOCUMENTATION_OR_ACCESS_BLOCKED'?'BLOCKED_BY_PARTICIPANT_ACCESS':raw;return <b className={status.includes('VERIFIED')?'demo-pass':'demo-warn'}><CheckCircle2/>{label(status)}</b>}
