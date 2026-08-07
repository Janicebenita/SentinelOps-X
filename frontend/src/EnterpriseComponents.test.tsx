import {QueryClientProvider} from '@tanstack/react-query';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {afterEach,describe,expect,it,vi} from 'vitest';
import ApprovalPage from './pages/ApprovalPage';
import ResourcePage from './pages/ResourcePage';
import {awaitingHumanRun,decidedRun,failedJson,newTestQueryClient,okJson} from './test/fixtures';

const mount=(node:React.ReactNode)=>render(<QueryClientProvider client={newTestQueryClient()}>{node}</QueryClientProvider>);
afterEach(()=>{cleanup();vi.restoreAllMocks();history.replaceState({},'','/')});

describe('approval and evidence integration boundaries',()=>{
 it('renders backend decision rejection and retains the production boundary',async()=>{
  history.replaceState({},'','/workflows/7/approval');
  vi.stubGlobal('fetch',vi.fn(async(input:RequestInfo|URL,init?:RequestInit)=>{
   const url=String(input);
   if(url.endsWith('/api/v1/workflows'))return okJson([awaitingHumanRun]);
   if(url.endsWith('/api/v1/auth/verify-role'))return okJson({verified:true,role:'SENIOR_DEVELOPER',permissions:['approve'],expires_at:'2026-08-05',verification_token:'signed-token'});
   if(url.endsWith('/approve')&&init?.method==='POST')return failedJson(409,'Verification Agent rejected approval readiness');
   return okJson({});
  }));
  mount(<ApprovalPage/>);
  fireEvent.change(screen.getByLabelText('Actor name'),{target:{value:'Senior QA'}});
  fireEvent.change(screen.getByLabelText('Trial access code'),{target:{value:'1111'}});
  fireEvent.click(screen.getByRole('button',{name:'Verify role'}));
  await screen.findByText(/VERIFIED ROLE: SENIOR DEVELOPER/);
  fireEvent.change(screen.getByLabelText('Mandatory rationale'),{target:{value:'Reviewed every mandatory gate.'}});
  fireEvent.click(screen.getByRole('button',{name:'Approve Recommendation'}));
  expect(await screen.findByText(/Backend request failed \(409\)/)).toBeTruthy();
  expect(screen.getByText('PRODUCTION ACTION: NOT EXECUTED')).toBeTruthy();
 });

 it('keeps Evidence ZIP locked before a governed human decision',async()=>{
  history.replaceState({},'','/workflows/7/export');
  vi.stubGlobal('fetch',vi.fn(async()=>okJson([awaitingHumanRun])));
  mount(<ResourcePage/>);
  expect(await screen.findByText(/Evidence export remains locked/)).toBeTruthy();
  expect((screen.getByRole('button',{name:/Export evidence ZIP/}) as HTMLButtonElement).disabled).toBe(true);
 });

 it('unlocks Evidence ZIP only when backend workflow state is DECIDED',async()=>{
  history.replaceState({},'','/workflows/7/export');
  vi.stubGlobal('fetch',vi.fn(async()=>okJson([decidedRun])));
  mount(<ResourcePage/>);
  expect(await screen.findByText(/recorded human decision enables/)).toBeTruthy();
  await waitFor(()=>expect((screen.getByRole('button',{name:/Export evidence ZIP/}) as HTMLButtonElement).disabled).toBe(false));
 });
});
