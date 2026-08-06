import {Fragment,useRef} from 'react';
import {ChevronRight} from 'lucide-react';
import type {JudgeDemoStage} from './types';
import StageExplanationPanel from './StageExplanationPanel';

export default function WorkflowStageRail({stages,selected,onSelect}:{stages:JudgeDemoStage[];selected:number;onSelect:(index:number)=>void}){
 const refs=useRef<(HTMLButtonElement|null)[]>([]);
 const key=(event:React.KeyboardEvent,index:number)=>{let next=index;if(event.key==='ArrowDown'||event.key==='ArrowRight')next=Math.min(stages.length-1,index+1);else if(event.key==='ArrowUp'||event.key==='ArrowLeft')next=Math.max(0,index-1);else if(event.key==='Home')next=0;else if(event.key==='End')next=stages.length-1;else return;event.preventDefault();onSelect(next);refs.current[next]?.focus()};
 return <div className="jd-rail" role="tablist" aria-label="SentinelOps workflow stages" aria-orientation="vertical">
  {stages.map((stage,index)=><Fragment key={stage.id}><div className="jd-stage-wrap">
   <button ref={node=>{refs.current[index]=node}} id={`stage-tab-${stage.id}`} type="button" role="tab" aria-expanded={selected===index} aria-selected={selected===index} aria-current={selected===index?'step':undefined} aria-controls="judge-stage-panel" tabIndex={selected===index?0:-1} className={`jd-stage ${selected===index?'selected':''}`} onClick={()=>onSelect(index)} onKeyDown={event=>key(event,index)}>
    <span className="jd-stage-number">{String(stage.order).padStart(2,'0')}</span><span className="jd-stage-label"><b>{stage.title}</b><small>{stage.shortDescription}</small>{stage.metric&&<strong>{stage.metric}</strong>}</span><ChevronRight aria-hidden="true"/>
   </button>
  </div>{selected===index&&<StageExplanationPanel stage={stage}/>}</Fragment>)}
 </div>;
}
