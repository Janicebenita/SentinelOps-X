import {useRef} from 'react';
import {ChevronRight} from 'lucide-react';
import type {StageView} from './types';
import StatusBadge from './StatusBadge';

export default function WorkflowStageRail({stages,selected,onSelect}:{stages:StageView[];selected:number;onSelect:(index:number)=>void}){
 const refs=useRef<(HTMLButtonElement|null)[]>([]);
 const key=(event:React.KeyboardEvent,index:number)=>{let next=index;if(event.key==='ArrowDown'||event.key==='ArrowRight')next=Math.min(stages.length-1,index+1);else if(event.key==='ArrowUp'||event.key==='ArrowLeft')next=Math.max(0,index-1);else if(event.key==='Home')next=0;else if(event.key==='End')next=stages.length-1;else return;event.preventDefault();onSelect(next);refs.current[next]?.focus()};
 return <div className="jd-rail" role="tablist" aria-label="SentinelOps workflow stages" aria-orientation="vertical">
  {stages.map((stage,index)=><div className="jd-stage-wrap" key={stage.id}>
   <button ref={node=>{refs.current[index]=node}} id={`stage-tab-${stage.id}`} type="button" role="tab" aria-selected={selected===index} aria-current={selected===index?'step':undefined} aria-controls="judge-stage-panel" tabIndex={selected===index?0:-1} className={`jd-stage ${selected===index?'selected':''}`} onClick={()=>onSelect(index)} onKeyDown={event=>key(event,index)}>
    <span className="jd-stage-number">{String(stage.number).padStart(2,'0')}</span><span className="jd-stage-label"><b>{stage.shortTitle}</b><StatusBadge status={stage.status}/></span><ChevronRight aria-hidden="true"/>
   </button>{index<stages.length-1&&<span className="jd-connector" aria-hidden="true"/>}
  </div>)}
 </div>;
}
