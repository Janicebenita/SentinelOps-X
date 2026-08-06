export type ArchitectureStatus='VERIFIED_LIVE'|'VERIFIED_LOCAL'|'IMPLEMENTED_REQUIRES_CREDENTIALS'|'LOCAL_ADAPTER_ONLY'|'FALLBACK_ACTIVE'|'BLOCKED_BY_PARTICIPANT_ACCESS'|'NOT_YET_EXECUTED'|'FAILED';

export const ARCHITECTURE_DOMAINS=['Product Experience','API and Authority','Agent Layer','Agent Protocols','AI Layer','Deterministic Intelligence','Data and Events','Google Cloud Runtime','Observability','Participant Boundary'] as const;
export type ArchitectureDomain=typeof ARCHITECTURE_DOMAINS[number];

export interface ArchitectureComponent{
 id:string;title:string;domain:ArchitectureDomain;purpose:string;whatItDoes:string;whyItMatters:string;
 inputs:string[];outputs:string[];authority:string;defaultStatus:ArchitectureStatus;integrationKey?:string;
 implemented:string[];missingEvidence:string[];evidence:string[];googleCloudServices:string[];security:string[];
 failureBehavior:string;fallback:string;related:string[];judgeTakeaway:string;boundary?:'deterministic'|'human'|'authenticated';
}

export interface IntegrationHealth{integration:string;status:string;last_health_check:string;configured_service:string;last_successful_call?:string;fallback_status:string;trace_id?:string;documentation:string;production_action:string}

export interface CloudRunServiceView{service:string;region:string;revision:string;url:string;health:string;readiness:string;authenticationMode:string;serviceAccount:string;status:ArchitectureStatus}
