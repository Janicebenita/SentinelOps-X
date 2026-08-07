import type {JudgeStageId} from './types';

export const JUDGE_DEMO_STAGE_DEFINITIONS=[
 {id:'problem',order:1,title:'Problem'},
 {id:'current-healthy-state',order:2,title:'Current healthy state'},
 {id:'rising-redis-pressure',order:3,title:'Rising Redis pressure'},
 {id:'safe-capacity-crossing',order:4,title:'Safe capacity crossing'},
 {id:'customer-impact-estimate',order:5,title:'Customer-impact estimate'},
 {id:'digital-twin',order:6,title:'Digital Twin'},
 {id:'scenario-progress',order:7,title:'Scenario progress'},
 {id:'intervention-tournament',order:8,title:'Intervention tournament'},
 {id:'fast-disqualification',order:9,title:'FAST disqualification'},
 {id:'gemini-reasoning',order:10,title:'Gemini reasoning'},
 {id:'gemma-policy-review',order:11,title:'Gemma policy review'},
 {id:'mandatory-safety-gates',order:12,title:'Mandatory Safety Gates'},
 {id:'verification-result',order:13,title:'Verification result'},
 {id:'executive-recommendation',order:14,title:'Executive recommendation'},
 {id:'human-boundary',order:15,title:'Human boundary'},
 {id:'intern-rejection',order:16,title:'Intern rejection'},
 {id:'senior-rationale',order:17,title:'Senior rationale'},
 {id:'audit-chain-update',order:18,title:'Audit-chain update'},
 {id:'evidence-zip',order:19,title:'Evidence ZIP'},
 {id:'google-cloud-evidence',order:20,title:'Google Cloud evidence'}
] as const satisfies ReadonlyArray<{id:JudgeStageId;order:number;title:string}>;

export const STAGE_IDS=JUDGE_DEMO_STAGE_DEFINITIONS.map(stage=>stage.id) as JudgeStageId[];
export const STAGE_BY_ID=new Map(JUDGE_DEMO_STAGE_DEFINITIONS.map(stage=>[stage.id,stage]));
