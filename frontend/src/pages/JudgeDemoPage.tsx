import {useMutation,useQuery,useQueryClient} from '@tanstack/react-query';
import {Activity,CheckCircle2,Play,ShieldCheck} from 'lucide-react';
import {nexusApi} from '../api/client';
import type {NexusRun} from '../types';

const label=(value:unknown)=>String(value??'NOT AVAILABLE').replaceAll('_',' ');
const yes=(value:unknown)=>value?<span className="demo-pass">YES</span>:<span className="demo-warn">NO</span>;

export default function JudgeDemoPage(){
 const cache=useQueryClient();
 const workflows=useQuery({queryKey:['judge-workflows'],queryFn:nexusApi.workflows});
 const run=workflows.data?.at(-1) as NexusRun|undefined;
 const integrations=useQuery({queryKey:['judge-integrations'],queryFn:nexusApi.integrations});
 const antigravity=useQuery({queryKey:['judge-antigravity'],queryFn:nexusApi.antigravity});
 const a2a=useQuery({queryKey:['judge-a2a',run?.id],queryFn:()=>nexusApi.a2a(run!.id),enabled:!!run});
 const audit=useQuery({queryKey:['judge-audit',run?.id],queryFn:()=>nexusApi.timeline(run!.id),enabled:!!run});
 const seed=useMutation({mutationFn:nexusApi.seed,onSuccess:()=>cache.invalidateQueries({queryKey:['judge-workflows']})});
 const execute=useMutation({mutationFn:()=>nexusApi.runAll(run!.id),onSuccess:()=>{cache.invalidateQueries({queryKey:['judge-workflows']});cache.invalidateQueries({queryKey:['judge-a2a']})}});
 const tournament=run?.tournament_json;
 const candidates=tournament?.candidates??[];
 const recommended=candidates.find(x=>x.candidate_id===tournament?.recommended_candidate_id);
 const fast=candidates.find(x=>x.candidate_id==='fast');
 const forecast=run?.forecast_json??{};
 const impact=run?.impact_json??{};
 const modelRows=integrations.data??[];
 const integration=(name:string)=>modelRows.find(x=>x.integration.toLowerCase().includes(name));
 const busy=seed.isPending||execute.isPending;
 return <div className="product-page judge-demo"><nav><a href="/"><b>SENTINELOPS NEXUS</b></a><a href="/command-centre">Command Centre</a><a href="/agents">AI Workforce</a></nav><main>
  <header className="judge-hero"><div><small>LIVE EVIDENCE WORKSPACE</small><h1>Judge Demo</h1><p>A curated view of persisted backend calculations and integration status. Nothing on this page approves or executes production changes.</p></div><div className="demo-actions"><button className="primary" onClick={()=>seed.mutate()} disabled={busy}><Play/>Create deterministic workflow</button><button className="primary" onClick={()=>execute.mutate()} disabled={!run||busy}><Activity/>Run backend workflow</button></div></header>
  {(workflows.isError||seed.isError||execute.isError)&&<p className="form-error">The backend workflow could not be loaded. Start the API and retry.</p>}
  <div className="demo-status"><b>Workflow {run?.id??'—'}</b><span>{label(run?.state??'NOT_STARTED')}</span><span>Seed {run?.seed??'—'}</span><span>{run?.production_action_executed?'UNSAFE':'PRODUCTION ACTION: NOT EXECUTED'}</span></div>
  <section className="judge-grid">
   <article><h2>1. Problem</h2><p>Reactive alerts discover Redis saturation after safe capacity is already threatened.</p><b>{label(run?.name)}</b></article>
   <article><h2>2. Current healthy state</h2><p>The seeded Payment Service begins below the reactive alert threshold.</p><b>{run?'VERIFIED LOCAL':'START WORKFLOW'}</b></article>
   <article><h2>3. Rising Redis pressure</h2><p>{label(forecast.equation)}</p><b>Safe threshold {label(forecast.safe_threshold_pct)}%</b></article>
   <article><h2>4. Safe capacity crossing</h2><p>Authoritative bounded linear forecast.</p><b>+{label(forecast.predicted_crossing_minutes)} minutes</b></article>
   <article><h2>5. Customer-impact estimate</h2><p>Operational estimate under visible assumptions.</p><b>+{label(forecast.predicted_customer_impact_minutes)} minutes · INR {Number(impact.revenue_exposure_inr??0).toLocaleString()}</b></article>
   <article><h2>6. Digital Twin</h2><p>Version-locked manifest with fixed seed.</p><b>{String(run?.twin_json?.manifest_hash??'NOT AVAILABLE').slice(0,16)}</b></article>
   <article><h2>7. Scenario progress</h2><p>Persisted deterministic counterfactual replays.</p><b>{run?.scenarios_json?.length??0} / 12 complete</b></article>
   <article><h2>8. Intervention tournament</h2><p>FAST / SAFE / OPTIMAL are scored server-side.</p><b>{candidates.map(x=>`${x.candidate_id}:${x.score}`).join(' · ')||'PENDING'}</b></article>
   <article><h2>9. FAST disqualification</h2><p>Mandatory failover safety overrides score.</p><b>{fast?yes(!fast.eligible):'NOT AVAILABLE'}</b></article>
   <article><h2>10. Gemini reasoning</h2><Status value={integration('gemini')?.status}/><small>Fallback is visibly distinguished from a managed call.</small></article>
   <article><h2>11. Gemma policy review</h2><Status value={integration('gemma')?.status}/><small>Policy critique cannot override gates.</small></article>
   <article><h2>12. Mandatory Safety Gates</h2><p>Eligibility is calculated by deterministic backend policy.</p><b>{recommended?recommended.gates.filter(g=>g.mandatory&&g.passed).length:'—'} passed</b></article>
   <article><h2>13. Verification result</h2><p>The Verification Agent checks evidence but never approves.</p><b>{run?.state==='AWAITING_HUMAN'||run?.state==='DECIDED'?'VERIFIED LOCAL':'PENDING'}</b></article>
   <article><h2>14. Executive recommendation</h2><p>Highest-scoring eligible candidate.</p><b>{label(recommended?.candidate_id)}</b></article>
   <article><h2>15. Human boundary</h2><p>The workflow stops before any production action.</p><b>{label(run?.state)}</b></article>
   <article><h2>16. Intern rejection</h2><p>Backend policy returns HTTP 403 for Intern approval.</p><b><a href={run?`/workflows/${run.id}/approval`:'/command-centre'}>Verify role manually</a></b></article>
   <article><h2>17. Senior rationale</h2><p>A verified Senior Developer still must enter a rationale.</p><b><a href={run?`/workflows/${run.id}/approval`:'/command-centre'}>Open approval stage</a></b></article>
   <article><h2>18. Audit-chain update</h2><p>Tamper-evident SHA-256-linked persisted events.</p><b>{String(audit.data?.at(-1)?.event_hash??'PENDING').slice(0,16)}</b></article>
   <article><h2>19. Evidence ZIP</h2><p>Export is unlocked only after the governed decision.</p><b>{run?.state==='DECIDED'?'AVAILABLE FOR VERIFICATION':'LOCKED'}</b></article>
   <article><h2>20. Google Cloud evidence</h2><p>Cloud Run revision: NOT AVAILABLE · BigQuery row: NOT AVAILABLE · Pub/Sub message: NOT AVAILABLE</p><Status value={integration('bigquery')?.status}/><small>A2A messages: {a2a.data?.length??0} · MCP: {label(integration('mcp')?.status)} · ADK: {label(integration('adk')?.status)} · Antigravity: {antigravity.data?.status==='DOCUMENTATION_OR_ACCESS_BLOCKED'?'BLOCKED_BY_PARTICIPANT_ACCESS':label(antigravity.data?.status)} · Audit event: {audit.data?.at(-1)?.id??'NOT AVAILABLE'}</small></article>
  </section>
  <section className="why-panel"><h2>Why this matters</h2><span>Customer impact surfaced: +{label(forecast.predicted_customer_impact_minutes)} min</span><span>Unsafe fix rejected: {fast&&!fast.eligible?'YES':'PENDING'}</span><span>Evidence generated: {audit.data?.length??0} audit events</span><span>Human authority preserved: YES</span></section>
  <div className="boundary"><ShieldCheck/> PRODUCTION ACTION: NOT EXECUTED</div>
 </main></div>
}

function Status({value}:{value?:string}){const raw=value??'REQUIRES_CREDENTIALS';const status=raw==='DOCUMENTATION_OR_ACCESS_BLOCKED'?'BLOCKED_BY_PARTICIPANT_ACCESS':raw;return <b className={status.includes('VERIFIED')?'demo-pass':'demo-warn'}><CheckCircle2/>{label(status)}</b>}
