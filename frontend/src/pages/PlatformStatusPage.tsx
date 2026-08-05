import {useQuery} from '@tanstack/react-query';
import {ShieldCheck} from 'lucide-react';
import {nexusApi} from '../api/client';

export default function PlatformStatusPage(){
 const query=useQuery({queryKey:['integration-health'],queryFn:nexusApi.integrations,refetchInterval:30000});
 const title=location.pathname==='/observability'?'Observability':location.pathname==='/security-status'?'Security Status':location.pathname==='/model-evaluation'?'Model Evaluation':'Integration Status';
 return <div className="product-page"><nav><a href="/"><b>SENTINELOPS NEXUS</b></a><a href="/command-centre">Command Centre</a></nav><main><h1>{title}</h1><p>Live backend-reported configuration and invocation evidence. Credential-required and local-adapter states are never shown as cloud-verified.</p><section>{query.isLoading&&<p>Checking backend integrations…</p>}{query.isError&&<p className="form-error">Integration status unavailable.</p>}{query.data?.map(item=><article className="workspace-card" key={item.integration}><h2>{item.integration}</h2><b>{item.status.replaceAll('_',' ')}</b><pre>{JSON.stringify(item,null,2)}</pre></article>)}</section><div className="boundary"><ShieldCheck/> PRODUCTION ACTION: NOT EXECUTED</div></main></div>
}
