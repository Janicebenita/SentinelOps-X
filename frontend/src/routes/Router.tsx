import {lazy,Suspense,useEffect,useState} from 'react';
const Landing=lazy(()=>import('../pages/LandingPage'));
const CommandCentre=lazy(()=>import('../App'));
const AgentPage=lazy(()=>import('../pages/AgentPage'));
const ApprovalPage=lazy(()=>import('../pages/ApprovalPage'));
const ResourcePage=lazy(()=>import('../pages/ResourcePage'));
const PlatformStatusPage=lazy(()=>import('../pages/PlatformStatusPage'));
const JudgeDemoPage=lazy(()=>import('../pages/JudgeDemoPage'));

export function navigate(path:string){history.pushState({},'',path);window.dispatchEvent(new PopStateEvent('popstate'))}
export default function Router(){const [path,setPath]=useState(location.pathname);useEffect(()=>{const change=()=>setPath(location.pathname);addEventListener('popstate',change);return()=>removeEventListener('popstate',change)},[]);let Page=Landing;if(path==='/command-centre')Page=CommandCentre;else if(path==='/judge-demo')Page=JudgeDemoPage;else if(path==='/agents'||path.startsWith('/agents/'))Page=AgentPage;else if(['/integrations','/observability','/security-status','/model-evaluation','/google-stack'].includes(path))Page=PlatformStatusPage;else if(/\/workflows\/\d+\/approval/.test(path))Page=ApprovalPage;else if(path!=='/')Page=ResourcePage;return <Suspense fallback={<div className="route-loading">Loading SentinelOps Nexus…<b>PRODUCTION ACTION: NOT EXECUTED</b></div>}><Page/></Suspense>}
