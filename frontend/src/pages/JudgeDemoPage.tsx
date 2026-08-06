import {useEffect,useMemo} from 'react';
import {useMutation,useQuery,useQueryClient} from '@tanstack/react-query';
import {Activity,Play,ShieldCheck,Sparkles} from 'lucide-react';
import {nexusApi} from '../api/client';
import {buildJudgeStages} from '../features/judge-demo/stageAdapter';
import GuidedControls from '../features/judge-demo/GuidedControls';
import StageExplanationPanel from '../features/judge-demo/StageExplanationPanel';
import WorkflowStageRail from '../features/judge-demo/WorkflowStageRail';
import {STAGE_IDS,type JudgeStageId} from '../features/judge-demo/types';
import {useGuidedPlayback} from '../features/judge-demo/useGuidedPlayback';
import '../features/judge-demo/judgeDemo.css';
import type {NexusRun} from '../types';

const initialStage=()=>{const value=new URLSearchParams(location.search).get('stage') as JudgeStageId|null;const index=value?STAGE_IDS.indexOf(value):-1;return index<0?0:index};
const updateStageUrl=(index:number)=>{const url=new URL(location.href);url.searchParams.set('stage',STAGE_IDS[index]);history.replaceState({},'',`${url.pathname}${url.search}${url.hash}`)};

export default function JudgeDemoPage(){
 const cache=useQueryClient();
 const workflows=useQuery({queryKey:['judge-workflows'],queryFn:nexusApi.workflows,staleTime:15_000,retry:1});
 const run=workflows.data?.at(-1) as NexusRun|undefined;
 const telemetry=useQuery({queryKey:['judge-telemetry',run?.id],queryFn:()=>nexusApi.telemetry(run!.id),enabled:Boolean(run),staleTime:15_000,retry:1});
 const evidence=useQuery({queryKey:['judge-evidence',run?.id],queryFn:()=>nexusApi.evidence(run!.id),enabled:Boolean(run),staleTime:15_000,retry:1});
 const audit=useQuery({queryKey:['judge-audit',run?.id],queryFn:()=>nexusApi.timeline(run!.id),enabled:Boolean(run),staleTime:15_000,retry:1});
 const verification=useQuery({queryKey:['judge-verification',run?.id],queryFn:()=>nexusApi.verificationResults(run!.id),enabled:Boolean(run),staleTime:15_000,retry:1});
 const a2a=useQuery({queryKey:['judge-a2a',run?.id],queryFn:()=>nexusApi.a2a(run!.id),enabled:Boolean(run),staleTime:30_000,retry:1});
 const integrations=useQuery({queryKey:['judge-integrations'],queryFn:nexusApi.integrations,staleTime:30_000,retry:1});
 const antigravity=useQuery({queryKey:['judge-antigravity'],queryFn:nexusApi.antigravity,staleTime:60_000,retry:1});
 const loading=[workflows,telemetry,evidence,audit,verification,integrations].some(query=>query.isLoading);
 const failed=[workflows,telemetry,evidence,audit,verification,integrations].some(query=>query.isError);
 const stages=useMemo(()=>buildJudgeStages({run,telemetry:telemetry.data,evidence:evidence.data,audit:audit.data,verification:verification.data,integrations:integrations.data,a2a:a2a.data,antigravity:antigravity.data,loading,failed}),[run,telemetry.data,evidence.data,audit.data,verification.data,integrations.data,a2a.data,antigravity.data,loading,failed]);
 const playback=useGuidedPlayback(stages.length,updateStageUrl,initialStage());
 const current=stages[playback.index]??stages[0];
 const refresh=()=>Promise.all(['judge-workflows','judge-telemetry','judge-evidence','judge-audit','judge-verification','judge-integrations','judge-a2a'].map(key=>cache.invalidateQueries({queryKey:[key]})));
 const seed=useMutation({mutationFn:nexusApi.seed,onSuccess:async()=>{await refresh();playback.select(0,false)}});
 const execute=useMutation({mutationFn:()=>nexusApi.runAll(run!.id),onSuccess:async()=>{await refresh();playback.restart()}});
 const busy=seed.isPending||execute.isPending;

 useEffect(()=>{const reduced=typeof matchMedia==='function'&&matchMedia('(prefers-reduced-motion: reduce)').matches;const panel=document.getElementById('judge-stage-panel');if(panel&&typeof panel.scrollIntoView==='function')panel.scrollIntoView({behavior:reduced?'auto':'smooth',block:'nearest'})},[playback.index]);
 useEffect(()=>{const pop=()=>playback.select(initialStage(),false);addEventListener('popstate',pop);return()=>removeEventListener('popstate',pop)},[]);

 return <div className="product-page judge-demo-v2"><nav><a href="/"><b>SENTINEL<span>OPS NEXUS</span></b></a><div><a href="/command-centre">Command Centre</a><a href="/agents">AI Workforce</a><a href="/architecture">Architecture</a></div></nav>
  <div className="jd-safety-pill"><ShieldCheck/> PRODUCTION ACTION: NOT EXECUTED</div>
  <main>
   <header className="jd-hero"><div><small>FIVE-MINUTE INTERACTIVE PRODUCT EXPERIENCE</small><h1>See tomorrow’s bottleneck.<br/><span>Intervene before impact.</span></h1><p>Explore every persisted calculation, AI explanation, deterministic gate, and human-control boundary. Select any stage or play the guided experience.</p><div className="jd-run-actions"><button className="primary" onClick={()=>seed.mutate()} disabled={busy}><Play/>{seed.isPending?'Creating workflow…':'Create deterministic workflow'}</button><button className="primary" onClick={()=>execute.mutate()} disabled={!run||busy}><Activity/>{execute.isPending?'Running 12 scenarios…':'Run backend workflow'}</button></div></div><div className="jd-hero-signal"><Sparkles/><small>LIVE WORKFLOW</small><strong>{run?.state?.replaceAll('_',' ')??'NOT YET STARTED'}</strong><span>Workflow {run?.id??'—'} · Seed {run?.seed??'—'}</span><b>{run?.production_action_executed?'FAILED':'SAFETY BOUNDARY ENFORCED'}</b></div></header>
   {failed&&<div className="jd-alert" role="alert"><b>Backend evidence is currently unavailable.</b><span>The experience explains each retained architecture stage, then labels its evidence state without fabricating success.</span></div>}
   <GuidedControls index={playback.index} total={stages.length} playing={playback.playing} guided={playback.guided} onPrevious={playback.previous} onNext={playback.next} onToggle={playback.toggle} onRestart={playback.restart} onExit={playback.exit}/>
   <section className="jd-workspace" aria-label="Interactive SentinelOps workflow"><WorkflowStageRail stages={stages} selected={playback.index} onSelect={playback.select}/><StageExplanationPanel key={current.id} stage={current}/></section>
   <section className="jd-google-lifecycle"><div><small>GOOGLE-NATIVE AI LIFECYCLE</small><p><b>Google AI Studio</b><i>→</i><b>Prompt Management</b><i>→</i><b>Prompt Evaluation</b><i>→</i><b>Gemini Runtime</b><i>→</i><b>Gemma Policy Review</b></p></div><div><small>DELIVERY AND RUNTIME</small><p><b>Cloud Build</b><i>→</i><b>Artifact Registry</b><i>→</i><b>Cloud Run</b></p><span>BigQuery · Pub/Sub · Secret Manager · Cloud Logging · Cloud Monitoring · Cloud Trace · IAM / Service Accounts</span></div></section>
   <div className="boundary"><ShieldCheck/> PRODUCTION ACTION: NOT EXECUTED</div>
  </main>
 </div>;
}
