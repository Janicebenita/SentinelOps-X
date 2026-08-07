import {useEffect,useState} from 'react';

export function useGuidedPlayback(length:number,onAdvance:(index:number,mode:'push'|'replace')=>void,initialIndex=0){
 const [index,setIndex]=useState(initialIndex); const [playing,setPlaying]=useState(false); const [guided,setGuided]=useState(true);
 const select=(next:number,manual=true)=>{const bounded=Math.max(0,Math.min(length-1,next));setIndex(bounded);onAdvance(bounded,manual?'push':'replace');if(manual)setPlaying(false)};
 useEffect(()=>{if(!playing||!guided)return;const timer=window.setTimeout(()=>{if(index>=length-1){setPlaying(false);return}select(index+1,false)},10000);return()=>window.clearTimeout(timer)},[guided,index,length,playing]);
 return {index,playing,guided,select,previous:()=>select(index-1),next:()=>select(index+1),toggle:()=>setPlaying(value=>!value),restart:()=>{setGuided(true);select(0,false);setPlaying(true)},exit:()=>{setPlaying(false);setGuided(false)}};
}
