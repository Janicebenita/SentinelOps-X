import type {NexusAuditV1,NexusCandidate,NexusEvidenceV1,NexusRun,NexusScenario,NexusTelemetry} from '../../types';

export const STAGE_IDS=['problem','healthy-state','redis-pressure','capacity-crossing','customer-impact','digital-twin','scenario-progress','intervention-tournament','fast-disqualification','gemini-reasoning','gemma-policy-review','mandatory-safety-gates','verification-result','executive-recommendation','human-boundary','intern-rejection','senior-rationale','audit-chain-update','evidence-zip','google-cloud-evidence'] as const;
export type JudgeStageId=typeof STAGE_IDS[number];
export type EvidenceStatus='VERIFIED_LIVE'|'VERIFIED_LOCAL'|'IMPLEMENTED_REQUIRES_CREDENTIALS'|'LOCAL_ADAPTER_ONLY'|'FALLBACK_ACTIVE'|'BLOCKED_BY_PARTICIPANT_ACCESS'|'NOT_YET_EXECUTED'|'FAILED';
export type StageFact={label:string;value:string;emphasis?:'good'|'warn'|'bad'};
export interface JudgeDemoStage{
 id:JudgeStageId;order:number;title:string;shortDescription:string;metric?:string;purpose:string;whatItDoes:string;whyItMatters:string;
 implemented:string[];missingForLiveOperation:string[];status:EvidenceStatus;liveData:StageFact[];evidenceReferences:string[];hashes:string[];timings:string[];
 assumptions:string[];safetyImplications:string[];googleCloudServices:string[];nextStageId?:JudgeStageId;judgeTakeaway:string;backendFieldMap?:Record<string,string>;href?:string;
 scenarios?:NexusScenario[];candidates?:NexusCandidate[];audit?:NexusAuditV1;telemetry?:NexusTelemetry;evidence?:NexusEvidenceV1[];
}
export type IntegrationHealth={integration:string;status:string;last_health_check:string;configured_service:string;last_successful_call?:string;fallback_status:string;trace_id?:string;documentation:string;production_action:string};
export type StageAdapterInput={run?:NexusRun;telemetry?:NexusTelemetry[];evidence?:NexusEvidenceV1[];audit?:NexusAuditV1[];verification?:Record<string,unknown>[];integrations?:IntegrationHealth[];a2a?:Record<string,unknown>[];antigravity?:{status:string;official_runtime_invoked:boolean;blocker:string;production_action:string};loading:boolean;failed:boolean};
