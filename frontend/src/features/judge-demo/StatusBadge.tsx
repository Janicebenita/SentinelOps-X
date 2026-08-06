import {CheckCircle2,Clock3,CloudOff,TriangleAlert} from 'lucide-react';
import type {EvidenceStatus} from './types';

export default function StatusBadge({status}:{status:EvidenceStatus}){
 const Icon=status.startsWith('VERIFIED')?CheckCircle2:status==='FAILED'?TriangleAlert:status==='NOT_YET_EXECUTED'?Clock3:CloudOff;
 return <span className={`jd-status ${status.toLowerCase().replaceAll('_','-')}`}><Icon aria-hidden="true"/>{status}</span>;
}
