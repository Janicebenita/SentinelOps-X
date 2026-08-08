import {useState} from 'react';
import {useMutation,useQuery,useQueryClient} from '@tanstack/react-query';
import {ShieldCheck} from 'lucide-react';
import {nexusApi} from '../api/client';
import type {RoleVerification} from '../types';
import Navbar from '../components/Navbar';

type DecisionKind='approve'|'reject'|'request-evidence';

export default function ApprovalPage(){
 const id=Number(location.pathname.split('/')[2]);
 const qc=useQueryClient();
 const run=useQuery({queryKey:['workflow',id],queryFn:()=>nexusApi.workflows().then(x=>x.find(r=>r.id===id)!)});
 const [actor,setActor]=useState('');const [code,setCode]=useState('');const [rationale,setRationale]=useState('');const [verified,setVerified]=useState<RoleVerification>();
 const verify=useMutation({mutationFn:()=>nexusApi.verifyRole(actor,code),onSuccess:data=>{setVerified(data);setCode('')}});
 const decide=useMutation({mutationFn:(kind:DecisionKind)=>nexusApi.decide(id,kind,{actor_name:actor,decision:kind==='request-evidence'?'request_more_evidence':kind,rationale,verification_token:verified!.verification_token}),onSuccess:()=>qc.invalidateQueries({queryKey:['workflow',id]})});
 const winner=run.data?.tournament_json.candidates.find(x=>x.candidate_id===run.data?.tournament_json.recommended_candidate_id);
 const gates=!!winner&&winner.eligible&&winner.gates.every(x=>!x.mandatory||x.passed);
 const awaiting=run.data?.state==='AWAITING_HUMAN';
 const canApprove=verified?.role==='SENIOR_DEVELOPER'&&gates&&awaiting&&rationale.trim().length>=3;
 const decisionLabel=decide.variables==='approve'?'APPROVED — HUMAN DECISION RECORDED':decide.variables==='reject'?'REJECTED — HUMAN DECISION RECORDED':'MORE EVIDENCE REQUESTED';
 return <div className="product-page"><Navbar/><main><h1>Human Approval Gateway</h1><p>The Verification Agent validates qualification and readiness. It never approves. Human approval authorizes the recommendation record and evidence export—not a production deployment.</p><section className="approval-form"><label>Actor name<input value={actor} onChange={e=>setActor(e.target.value)} autoComplete="name"/></label><label>Trial access code<input value={code} onChange={e=>setCode(e.target.value)} type="password" autoComplete="one-time-code"/></label><button onClick={()=>verify.mutate()} disabled={actor.length<2||code.length<4||verify.isPending}>{verify.isPending?'Verifying role…':'Verify role'}</button>{verify.isError&&<p className="form-error">{verify.error.message}</p>}{verified&&<div className={`role-badge ${verified.role.toLowerCase()}`}><ShieldCheck/> VERIFIED ROLE: {verified.role.replace('_',' ')}</div>}<label>Mandatory rationale<textarea value={rationale} onChange={e=>setRationale(e.target.value)} rows={4}/></label><div className="decision-actions"><button disabled={!canApprove||decide.isPending} onClick={()=>decide.mutate('approve')}>Approve Recommendation</button><button disabled={!verified||!awaiting||rationale.trim().length<3||decide.isPending} onClick={()=>decide.mutate('reject')}>Reject Recommendation</button><button disabled={!verified||!awaiting||rationale.trim().length<3||decide.isPending} onClick={()=>decide.mutate('request-evidence')}>Request More Evidence</button></div>{verified?.role==='INTERN'&&<p className="form-warning">Intern users may inspect, reject or request evidence, but cannot approve.</p>}{decide.isSuccess&&<div className="form-success decision-confirmation"><strong>{decisionLabel}</strong><span>The decision is audited and evidence-controlled. Production systems were intentionally not changed.</span></div>}{decide.isError&&<p className="form-error">{decide.error.message}</p>}</section><div className="boundary"><ShieldCheck/><span>DECISION STATUS: {decide.isSuccess?'RECORDED':'PENDING'}</span> · <strong>PRODUCTION ACTION: NOT EXECUTED</strong></div></main></div>;
}
