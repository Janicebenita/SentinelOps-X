import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Download, ShieldCheck, FileText, Lock, ArrowLeft, CheckCircle2, TriangleAlert, Compass, Play } from 'lucide-react';
import { nexusApi } from '../api/client';
import { navigate } from '../routes/Router';
import Navbar from '../components/Navbar';
import type { NexusEvidenceV1, NexusAuditV1 } from '../types';

export default function ResourcePage() {
  const path = location.pathname;
  const idMatch = path.match(/\/workflows\/(\d+)/);
  const id = idMatch ? Number(idMatch[1]) : 1;

  const workflows = useQuery({ queryKey: ['workflows'], queryFn: nexusApi.workflows });
  const run = workflows.data?.find(x => x.id === id) || workflows.data?.[0];

  const evidence = useQuery({
    queryKey: ['evidence', id],
    queryFn: () => nexusApi.evidence(id),
    enabled: !!id && path.includes('/evidence'),
  });

  const audit = useQuery({
    queryKey: ['timeline', id],
    queryFn: () => nexusApi.timeline(id),
    enabled: !!id && path.includes('/audit'),
  });

  const verification = useQuery({
    queryKey: ['verification', id],
    queryFn: () => nexusApi.verificationResults(id),
    enabled: !!id && path.includes('/verification'),
  });

  const exportEvidence = useMutation({ mutationFn: () => nexusApi.downloadEvidence(id) });

  // Route 1: Documentation Page (/docs)
  if (path === '/docs') {
    return <DocsPage />;
  }

  // Route 2: Safety & Governance Page (/safety)
  if (path === '/safety') {
    return <SafetyPage />;
  }

  // Route 3: Workflow Evidence Explorer (/workflows/:id/evidence)
  if (path.includes('/evidence')) {
    return (
      <PageShell title={`Workflow #${id} Evidence Explorer`}>
        <div className="resource-header-bar">
          <p>Each material operational claim in SentinelOps Nexus references persisted, SHA-256 hashed evidence.</p>
        </div>
        {evidence.isLoading && <p className="loading-state">Loading persisted evidence records...</p>}
        {evidence.isError && <p className="form-error">Failed to load evidence: {String(evidence.error)}</p>}
        {evidence.data && (
          <div className="evidence-table-wrapper">
            <table className="nexus-data-table">
              <thead>
                <tr>
                  <th>Evidence ID</th>
                  <th>Source Component</th>
                  <th>Summary</th>
                  <th>Content SHA-256 Hash</th>
                </tr>
              </thead>
              <tbody>
                {(evidence.data as NexusEvidenceV1[]).map(item => (
                  <tr key={item.evidence_id || item.id}>
                    <td><code>{item.evidence_id || item.id}</code></td>
                    <td><span className="source-tag">{item.source}</span></td>
                    <td>{item.summary}</td>
                    <td><code className="hash-code">{item.content_hash}</code></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </PageShell>
    );
  }

  // Route 4: Audit Timeline (/workflows/:id/audit)
  if (path.includes('/audit')) {
    return (
      <PageShell title={`Workflow #${id} Audit Chain Timeline`}>
        <div className="resource-header-bar">
          <p>Chained SHA-256 audit events persisted directly by the FastAPI backend workflow engine.</p>
        </div>
        {audit.isLoading && <p className="loading-state">Loading audit event chain...</p>}
        {audit.isError && <p className="form-error">Failed to load audit events: {String(audit.error)}</p>}
        {audit.data && (
          <div className="audit-timeline-container">
            {(audit.data as NexusAuditV1[]).map((evt) => (
              <div key={evt.sequence || evt.id} className="audit-timeline-card">
                <div className="audit-seq">#{evt.sequence || evt.id}</div>
                <div className="audit-details">
                  <div className="audit-type-row">
                    <span className="audit-type">{evt.event_type}</span>
                    <span className="audit-actor">Actor: {evt.actor}</span>
                  </div>
                  <div className="audit-hash">
                    <span>SHA-256 Event Hash:</span> <code>{evt.event_hash}</code>
                  </div>
                  {evt.previous_hash && (
                    <div className="audit-prev-hash">
                      <span>Prev Hash:</span> <code>{evt.previous_hash}</code>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </PageShell>
    );
  }

  // Route 5: Verification Results (/workflows/:id/verification)
  if (path.includes('/verification')) {
    return (
      <PageShell title={`Workflow #${id} Verification Results`}>
        <div className="resource-header-bar">
          <p>Technical readiness, gate eligibility, and approver qualification checks performed by the Verification Agent.</p>
        </div>
        {verification.isLoading && <p className="loading-state">Loading verification checks...</p>}
        {verification.isError && <p className="form-error">Failed to load verification results: {String(verification.error)}</p>}
        {verification.data && (
          <div className="verification-grid">
            {(verification.data as Record<string, any>[]).map((res, index) => (
              <div key={String(res.check_id || index)} className={`verification-card ${res.passed ? 'pass' : 'fail'}`}>
                <div className="ver-status">
                  {res.passed ? <CheckCircle2 className="w-5 h-5 text-emerald-400" /> : <TriangleAlert className="w-5 h-5 text-amber-400" />}
                  <span className="check-name">{String(res.check_name || 'Verification Check')}</span>
                </div>
                <p className="check-details">{String(res.details || '')}</p>
                <div className="check-meta">
                  <span>Category: {String(res.category || 'General')}</span>
                  {res.check_hash && <code>Hash: {String(res.check_hash).slice(0, 12)}</code>}
                </div>
              </div>
            ))}
          </div>
        )}
      </PageShell>
    );
  }

  // Route 6: Evidence Export (/workflows/:id/export)
  if (path.includes('/export')) {
    const isDecided = run?.state === 'DECIDED';
    const exportText = isDecided
      ? 'A recorded human decision enables one evidence download.'
      : 'Evidence export remains locked until an authorized human decision is recorded.';

    return (
      <PageShell title={`Workflow #${id} Evidence Export`}>
        <div className="export-workspace-card">
          <Download className="w-12 h-12 text-cyan-400 mb-4" />
          <h2>Tamper-Evident Evidence Package</h2>
          <p className="mb-4">
            {exportText}
          </p>

          <button
            className="primary export-btn"
            disabled={!isDecided || exportEvidence.isPending}
            onClick={() => exportEvidence.mutate()}
          >
            <Download className="w-4 h-4 mr-2" />
            {exportEvidence.isPending ? 'Preparing evidence…' : 'Export evidence ZIP'}
          </button>

          {exportEvidence.isError && <p className="form-error mt-4">{exportEvidence.error.message}</p>}
        </div>
      </PageShell>
    );
  }

  // Route 7: Workflow Root (/workflows/:id)
  if (path.startsWith('/workflows/')) {
    return (
      <PageShell title={`Workflow #${id} Overview`}>
        <div className="workflow-overview-grid">
          <div className="workspace-card">
            <h3>Workflow Metadata</h3>
            <pre>{JSON.stringify({ id: run?.id, state: run?.state, seed: run?.seed, created_at: run?.created_at }, null, 2)}</pre>
          </div>
          <div className="workspace-card">
            <h3>Quick Actions</h3>
            <div className="workflow-nav-buttons">
              <button onClick={() => navigate(`/workflows/${id}/approval`)}>Human Approval</button>
              <button onClick={() => navigate(`/workflows/${id}/evidence`)}>Evidence Explorer</button>
              <button onClick={() => navigate(`/workflows/${id}/audit`)}>Audit Chain</button>
              <button onClick={() => navigate(`/workflows/${id}/verification`)}>Verification Results</button>
              <button onClick={() => navigate(`/workflows/${id}/export`)}>Export Package</button>
            </div>
          </div>
        </div>
      </PageShell>
    );
  }

  // Route 8: 404 Not Found Page (Unmatched paths)
  return (
    <div className="product-page">
      <Navbar />
      <main className="not-found-container">
        <div className="not-found-card">
          <TriangleAlert className="w-16 h-16 text-amber-400 mb-4" />
          <h1>404 - Page Not Found</h1>
          <p>The operational path <code>{path}</code> does not exist in SentinelOps Nexus.</p>
          <div className="not-found-actions">
            <button className="primary" onClick={() => navigate('/command-centre')}>
              <Compass className="w-4 h-4 mr-2" />
              Open Command Centre
            </button>
            <button onClick={() => navigate('/judge-demo')}>
              <Play className="w-4 h-4 mr-2" />
              Start Guided Demo
            </button>
          </div>
        </div>
        <div className="boundary"><ShieldCheck /> PRODUCTION ACTION: NOT EXECUTED</div>
      </main>
    </div>
  );
}

// Shell layout helper
function PageShell({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="product-page">
      <Navbar />
      <main className="resource-page-main">
        <div className="resource-page-header">
          <button className="back-btn" onClick={() => navigate('/command-centre')}>
            <ArrowLeft className="w-4 h-4 mr-1" /> Back to Command Centre
          </button>
          <h1>{title}</h1>
        </div>
        <div className="resource-content">{children}</div>
        <div className="boundary"><ShieldCheck /> PRODUCTION ACTION: NOT EXECUTED</div>
      </main>
    </div>
  );
}

// Dedicated Documentation Page Component (/docs)
function DocsPage() {
  const [tab, setTab] = useState<'overview' | 'api' | 'prompts' | 'setup'>('overview');

  return (
    <div className="product-page">
      <Navbar />
      <main className="resource-page-main">
        <div className="resource-page-header">
          <h1>🛡️ SentinelOps Nexus Documentation</h1>
          <p>Evidence-driven Enterprise Operational Digital Twin for predicting Redis saturation and governed interventions.</p>
        </div>

        <div className="docs-tab-rail">
          <button className={tab === 'overview' ? 'active' : ''} onClick={() => setTab('overview')}>Architecture Overview</button>
          <button className={tab === 'api' ? 'active' : ''} onClick={() => setTab('api')}>API Endpoints</button>
          <button className={tab === 'prompts' ? 'active' : ''} onClick={() => setTab('prompts')}>Google AI & Prompts</button>
          <button className={tab === 'setup' ? 'active' : ''} onClick={() => setTab('setup')}>Local Quickstart</button>
        </div>

        <div className="docs-tab-content">
          {tab === 'overview' && (
            <div className="docs-section">
              <h2>Architecture Overview</h2>
              <p>SentinelOps Nexus executes an 11-stage safety-first workflow:</p>
              <ol className="docs-step-list">
                <li><strong>Telemetry Ingestion:</strong> Reads payment service Redis memory pressure and checkout latency.</li>
                <li><strong>Bounded Forecast:</strong> Predicts safe-capacity crossing (+30m) before customer impact (+45m).</li>
                <li><strong>Digital Twin Engine:</strong> Content-hashes operational state and baseline parameters.</li>
                <li><strong>Simulation & Tournament:</strong> Replays 12 deterministic scenarios across FAST, SAFE, and OPTIMAL strategies.</li>
                <li><strong>Mandatory Safety Gates:</strong> Eligibility overrides heuristics; FAST is disqualified by failover gate.</li>
                <li><strong>Verification Agent:</strong> Validates technical readiness and human approver authorization.</li>
                <li><strong>Human Decision Boundary:</strong> Workflow pauses at <code>AWAITING_HUMAN</code>; approval requires verified Senior Developer and rationale.</li>
              </ol>
            </div>
          )}

          {tab === 'api' && (
            <div className="docs-section">
              <h2>Key REST API Endpoints</h2>
              <div className="api-endpoint-list">
                <div className="api-endpoint-card">
                  <span className="method get">GET</span> <code>/api/v1/workflows</code>
                  <p>Lists all persisted operational workflows and current state.</p>
                </div>
                <div className="api-endpoint-card">
                  <span className="method post">POST</span> <code>/api/v1/workflows/bootstrap</code>
                  <p>Seeds deterministic payment telemetry, creates a workflow, and executes all 12 scenarios.</p>
                </div>
                <div className="api-endpoint-card">
                  <span className="method post">POST</span> <code>/api/v1/auth/verify-role</code>
                  <p>Verifies user identity, role (INTERN vs SENIOR_DEVELOPER), and issues JWT token.</p>
                </div>
                <div className="api-endpoint-card">
                  <span className="method post">POST</span> <code>/api/v1/workflows/{'{id}'}/decide</code>
                  <p>Submits a human decision (approve, reject, request_more_evidence) with mandatory rationale.</p>
                </div>
                <div className="api-endpoint-card">
                  <span className="method get">GET</span> <code>/api/v1/workflows/{'{id}'}/export-evidence</code>
                  <p>Downloads tamper-evident Evidence ZIP package with <code>manifest.sha256</code>.</p>
                </div>
              </div>
            </div>
          )}

          {tab === 'prompts' && (
            <div className="docs-section">
              <h2>Google AI Studio & Prompt Lifecycle</h2>
              <p>SentinelOps Nexus enforces strict model boundaries:</p>
              <ul>
                <li><strong>Gemini Enterprise Platform:</strong> Generates evidence-grounded executive summaries and candidate trade-off explanations.</li>
                <li><strong>Gemma Private Policy Review:</strong> Provides secondary policy critique on safety gate adherence.</li>
                <li><strong>Authority Invariant:</strong> Neither model can approve recommendations, mutate state, or execute infrastructure commands.</li>
              </ul>
            </div>
          )}

          {tab === 'setup' && (
            <div className="docs-section">
              <h2>Local Development Quickstart</h2>
              <pre className="code-block">
{`# Start application services
python scripts/run_demo.py

# Access local endpoints
Frontend UI: http://localhost:5173/
API Server:  http://localhost:8000/docs
Demo Target: http://localhost:8001/`}
              </pre>
            </div>
          )}
        </div>

        <div className="boundary"><ShieldCheck /> PRODUCTION ACTION: NOT EXECUTED</div>
      </main>
    </div>
  );
}

// Dedicated Safety & Governance Page Component (/safety)
function SafetyPage() {
  return (
    <div className="product-page">
      <Navbar />
      <main className="resource-page-main">
        <div className="resource-page-header">
          <h1>🛡️ Safety, Governance & Authority Boundaries</h1>
          <p>SentinelOps Nexus is a human-governed decision support system. It contains no production-execution code.</p>
        </div>

        <div className="safety-grid-container">
          <div className="safety-card highlight">
            <Lock className="w-8 h-8 text-amber-400 mb-2" />
            <h2>Strict Safety Invariant</h2>
            <strong className="safety-badge-large">PRODUCTION ACTION: NOT EXECUTED</strong>
            <p>
              Human approval records a governed, audited decision and enables evidence export. It does not scale, restart, roll back, reconfigure, or touch live cloud infrastructure.
            </p>
          </div>

          <div className="safety-card">
            <h2>Role-Based Authority (RBAC)</h2>
            <div className="role-rule">
              <span className="role-tag intern">INTERN (Code 0000)</span>
              <p>May inspect telemetry, run scenarios, and request evidence. Cannot approve recommendations.</p>
            </div>
            <div className="role-rule">
              <span className="role-tag senior">SENIOR DEVELOPER (Code 1111)</span>
              <p>May approve recommendations only after mandatory rationale entry and SHA-256 gate validation.</p>
            </div>
          </div>

          <div className="safety-card">
            <h2>Mandatory Safety Gates</h2>
            <p>
              Candidates are evaluated against deterministic safety gates. A candidate that fails a mandatory gate (e.g. FAST failing failover check) is instantly <strong>DISQUALIFIED</strong> regardless of heuristic score.
            </p>
          </div>

          <div className="safety-card">
            <h2>Verification Agent Boundary</h2>
            <p>
              The Verification Agent validates environment readiness, technical checks, and approver qualification. It has zero approval authority and cannot modify workflow state.
            </p>
          </div>
        </div>

        <div className="boundary"><ShieldCheck /> PRODUCTION ACTION: NOT EXECUTED</div>
      </main>
    </div>
  );
}
