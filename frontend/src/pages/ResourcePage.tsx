import {useMutation,useQuery} from '@tanstack/react-query';
import {Download,ShieldCheck} from 'lucide-react';
import {nexusApi} from '../api/client';

export default function ResourcePage(){
 const path=location.pathname;const id=Number(path.split('/')[2]);
 const workflows=useQuery({queryKey:['workflows'],queryFn:nexusApi.workflows});
 const run=workflows.data?.find(x=>x.id===id)||workflows.data?.[0];
 const evidence=useQuery({queryKey:['evidence',id],queryFn:()=>nexusApi.evidence(id),enabled:!!id&&path.includes('/evidence')});
 const audit=useQuery({queryKey:['timeline',id],queryFn:()=>nexusApi.timeline(id),enabled:!!id&&path.includes('/audit')});
 const verification=useQuery({queryKey:['verification',id],queryFn:()=>nexusApi.verificationResults(id),enabled:!!id&&path.includes('/verification')});
 const exportEvidence=useMutation({mutationFn:()=>nexusApi.downloadEvidence(id)});
 let title='SentinelOps Nexus Documentation';let body:unknown={routes:['/command-centre','/agents','/architecture','/safety','/docs']};
 if(path==='/architecture'){title='Architecture';body={flow:'React routes → FastAPI → deterministic workflow services → SQLAlchemy artifacts → SHA-256 audit chain',boundary:'No cloud or production execution adapter exists.'}}
 else if(path==='/safety'){title='Safety and Governance';body={intern:'Cannot approve',senior_developer:'May approve with a short-lived verified token and rationale',verification_agent:'Verifies but never approves',production_action:'NOT EXECUTED'}}
 else if(path.includes('/evidence')){title='Evidence Explorer';body=evidence.data??(evidence.isLoading?'Loading persisted evidence…':evidence.error?.message)}
 else if(path.includes('/audit')){title='Audit Timeline';body=audit.data??(audit.isLoading?'Loading chained audit events…':audit.error?.message)}
 else if(path.includes('/verification')){title='Verification Results';body=verification.data??(verification.isLoading?'Loading persisted verification records…':verification.error?.message)}
 else if(path.includes('/export')){title='Evidence Export';body=run?.state==='DECIDED'?'A recorded human decision enables one evidence download.':'Evidence export remains locked until an authorized human decision is recorded.'}
 else if(path.startsWith('/workflows/')){title=`Workflow ${id}`;body=run}
 return <div className="product-page"><nav><a href="/"><b>SENTINELOPS NEXUS</b></a><a href="/command-centre">Command Centre</a></nav><main><h1>{title}</h1><article className="workspace-card"><pre>{typeof body==='string'?body:JSON.stringify(body,null,2)}</pre>{path.includes('/export')&&<button className="primary" disabled={run?.state!=='DECIDED'||exportEvidence.isPending} onClick={()=>exportEvidence.mutate()}><Download/>{exportEvidence.isPending?'Preparing evidence…':'Export evidence ZIP'}</button>}{exportEvidence.isError&&<p className="form-error">{exportEvidence.error.message}</p>}</article><div className="boundary"><ShieldCheck/> PRODUCTION ACTION: NOT EXECUTED</div></main></div>;
}
