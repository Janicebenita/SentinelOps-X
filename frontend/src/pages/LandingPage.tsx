import { ArrowRight, CheckCircle2, Network, ShieldCheck } from 'lucide-react';
import { navigate } from '../routes/Router';
import Navbar from '../components/Navbar';

const capabilities = [
  'Deterministic forecasting',
  'Bounded Digital Twin',
  '12-scenario simulation',
  'FAST / SAFE / OPTIMAL tournament',
  'Mandatory safety gates',
  'Verification Agent',
  'Role-based approval',
  'SHA-256 audit chain',
  'Evidence package',
];

export default function LandingPage() {
  return (
    <div className="landing">
      <Navbar />
      <main>
        <section className="landing-hero">
          <small>THE ENTERPRISE OPERATIONAL DIGITAL TWIN</small>
          <h1>Predict tomorrow’s operational bottleneck before customers experience it.</h1>
          <p>Observe, predict, simulate, verify, rank and explain interventions—then stop at an authorized human decision.</p>
          <div>
            <button onClick={() => navigate('/command-centre')}>
              Open Command Centre <ArrowRight />
            </button>
            <button onClick={() => navigate('/judge-demo')}>Start Guided Demo</button>
            <button onClick={() => navigate('/architecture')}>View Architecture</button>
          </div>
        </section>
        <section className="landing-grid">
          <article>
            <h2>The operational problem</h2>
            <p>Reactive monitoring detects incidents late. Intervention choices remain uncertain and evidence is fragmented across tools.</p>
          </article>
          <article>
            <h2>The Nexus approach</h2>
            <p>One bounded workflow connects observed evidence to forecast, Digital Twin, scenarios, verification, ranked strategies and human review.</p>
          </article>
        </section>
        <section>
          <h2>Enterprise capabilities</h2>
          <div className="capability-grid">
            {capabilities.map((x) => (
              <span key={x}>
                <CheckCircle2 />
                {x}
              </span>
            ))}
          </div>
        </section>
        <section className="landing-safety">
          <ShieldCheck />
          <div>
            <h2>Human-controlled by design</h2>
            <p>Interns cannot approve. A verified Senior Developer and rationale are required. The Verification Agent checks readiness but never approves.</p>
            <b>PRODUCTION ACTION: NOT EXECUTED</b>
          </div>
        </section>
        <section className="landing-grid">
          <article>
            <Network />
            <h2>Architecture</h2>
            <p>React routes call a typed FastAPI workflow over persisted SQLAlchemy artifacts and chained audit evidence.</p>
            <a href="/architecture">View full architecture</a>
          </article>
          <article>
            <h2>Deterministic Guided Demo</h2>
            <p>No paid AI key or external AI dependency is required. The canonical seed is reproducible.</p>
            <button onClick={() => navigate('/judge-demo')}>Open evidence workspace</button>
          </article>
        </section>
      </main>
      <footer>
        <a href="https://github.com/Janicebenita/SentinelOps-X">GitHub</a>
        <a href="/docs">Documentation</a>
        <a href="/safety">Limitations & safety</a>
        <span>Built by Janice Benita F</span>
      </footer>
    </div>
  );
}
