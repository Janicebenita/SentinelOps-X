import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {afterEach,describe,expect,it,vi} from 'vitest';
import LandingPage from './pages/LandingPage';
import ApprovalPage from './pages/ApprovalPage';

const run={id:7,state:'RECOMMENDED',tournament_json:{recommended_candidate_id:'optimal',candidates:[{candidate_id:'optimal',eligible:true,gates:[{mandatory:true,passed:true}]}]}};
afterEach(()=>{cleanup();vi.restoreAllMocks();history.replaceState({},'','/')});
const wrap=(node:React.ReactNode)=>render(<QueryClientProvider client={new QueryClient()}>{node}</QueryClientProvider>);

describe('upgrade routes and authorization UX',()=>{
 it('renders the fast product landing page and safety boundary',()=>{wrap(<LandingPage/>);expect(screen.getByText('Predict tomorrow’s operational bottleneck before customers experience it.')).toBeTruthy();expect(screen.getByText('PRODUCTION ACTION: NOT EXECUTED')).toBeTruthy();expect(screen.getByRole('button',{name:/Open Command Centre/})).toBeTruthy()});
 it('shows Intern role and keeps approval disabled',async()=>{history.replaceState({},'','/workflows/7/approval');vi.stubGlobal('fetch',vi.fn(async(input:RequestInfo|URL)=>({ok:true,json:async()=>String(input).includes('verify-role')?{verified:true,role:'INTERN',permissions:['reject'],expires_at:'2026-08-05',verification_token:'signed-token-value'}:[run]}) as Response));wrap(<ApprovalPage/>);fireEvent.change(screen.getByLabelText('Actor name'),{target:{value:'Intern User'}});fireEvent.change(screen.getByLabelText('Trial access code'),{target:{value:'0000'}});fireEvent.click(screen.getByRole('button',{name:'Verify role'}));expect(await screen.findByText(/VERIFIED ROLE: INTERN/)).toBeTruthy();expect((screen.getByRole('button',{name:'Approve Recommendation'}) as HTMLButtonElement).disabled).toBe(true)});
 it('enables Senior Developer approval only after rationale',async()=>{history.replaceState({},'','/workflows/7/approval');vi.stubGlobal('fetch',vi.fn(async(input:RequestInfo|URL)=>({ok:true,json:async()=>String(input).includes('verify-role')?{verified:true,role:'SENIOR_DEVELOPER',permissions:['approve'],expires_at:'2026-08-05',verification_token:'signed-token-value'}:[run]}) as Response));wrap(<ApprovalPage/>);fireEvent.change(screen.getByLabelText('Actor name'),{target:{value:'Senior User'}});fireEvent.change(screen.getByLabelText('Trial access code'),{target:{value:'1111'}});fireEvent.click(screen.getByRole('button',{name:'Verify role'}));await screen.findByText(/VERIFIED ROLE: SENIOR DEVELOPER/);expect((screen.getByRole('button',{name:'Approve Recommendation'}) as HTMLButtonElement).disabled).toBe(true);fireEvent.change(screen.getByLabelText('Mandatory rationale'),{target:{value:'All gates reviewed.'}});await waitFor(()=>expect((screen.getByRole('button',{name:'Approve Recommendation'}) as HTMLButtonElement).disabled).toBe(false))});
});
