import type {NexusAuditV1,NexusCandidate,NexusEvidenceV1,NexusRun,NexusScenario,NexusTelemetry} from '../../types';

export const STAGE_IDS=['telemetry','forecast','digital-twin','simulation','optimization','gemini','gemma','safety-gates','verification','executive','awaiting-human','human-approval','audit-chain','evidence-zip','google-cloud'] as const;
export type JudgeStageId=typeof STAGE_IDS[number];
export type DemoStatus='VERIFIED_LIVE'|'VERIFIED_LOCAL'|'FALLBACK_ACTIVE'|'REQUIRES_CREDENTIALS'|'BLOCKED_BY_PARTICIPANT_ACCESS'|'FAILED'|'NOT_YET_EXECUTED';
export type StageFact={label:string;value:string;emphasis?:'good'|'warn'|'bad'};
export type StageView={
 id:JudgeStageId; number:number; title:string; shortTitle:string; summary:string; why:string; status:DemoStatus;
 inputs:StageFact[]; outputs:StageFact[]; evidenceIds:string[]; resultHash:string; traceId:string; latency:string;
 safetyRule:string; googleService:string; fallbackState:DemoStatus; takeaway:string; nextStage:string; href?:string;
 scenarios?:NexusScenario[]; candidates?:NexusCandidate[]; audit?:NexusAuditV1; telemetry?:NexusTelemetry; evidence?:NexusEvidenceV1[];
};
export type IntegrationHealth={integration:string;status:string;last_health_check:string;configured_service:string;last_successful_call?:string;fallback_status:string;trace_id?:string;documentation:string;production_action:string};
export type StageAdapterInput={
 run?:NexusRun; telemetry?:NexusTelemetry[]; evidence?:NexusEvidenceV1[]; audit?:NexusAuditV1[];
 verification?:Record<string,unknown>[]; integrations?:IntegrationHealth[]; a2a?:Record<string,unknown>[];
 antigravity?:{status:string;official_runtime_invoked:boolean;blocker:string;production_action:string};
 loading:boolean; failed:boolean;
};
