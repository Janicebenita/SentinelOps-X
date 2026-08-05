# Making SentinelOps Nexus: A Human-Led Engineering Write-up

## Why the project was created

SentinelOps Nexus began with a human observation: operational teams often learn about a capacity bottleneck only after customer latency or errors cross an alert threshold. The project was created to explain a better operating model in software—not as a video or slide deck. The human creator defined the problem, safety boundary, workflow, evaluation questions and product behavior, then used AI-assisted engineering as an implementation partner. Every product decision, test expectation, correction and deployment remained human-directed.

The central promise became: **predict tomorrow’s operational bottleneck before customers experience it.** The product models a Payment Service approaching Redis saturation, forecasts the safe-capacity crossing, creates a bounded Digital Twin, evaluates 12 deterministic scenarios, compares FAST/SAFE/OPTIMAL interventions and stops at a human decision.

## How the human guided the build

The human creator repeatedly tested the actual Render application by clicking controls, changing presets, uploading JSON, approving decisions and examining evidence. Screenshots were used to identify discrepancies between intended behavior and visible software. Requirements were refined in plain operational language: make it a practical product, keep manual intervention, make buttons visibly actionable, ensure calculations propagate, make approval status truthful and keep the narrated video separate.

AI assistance was used to inspect code, implement changes, run tests and automate deployments, but it did not define business authority. The human specified that models and agents must never approve or execute production changes. The result is therefore best described as **human-generated product direction with AI-assisted software engineering**.

## Architecture and implementation

The frontend uses React, TypeScript, TanStack Query and route-level lazy loading. FastAPI exposes strict Pydantic v2 contracts. SQLAlchemy persists workflow, evidence, agent execution, verification, role and decision records. Deterministic Python calculations generate telemetry, forecasts, Twin hashes, scenarios, tournament scores and impact estimates. Audit events form a SHA-256 previous/current hash chain.

The current workforce includes Orchestrator, Observer, Evidence, Process Discovery, Prediction, Digital Twin, Simulation, Optimization, Verification, Business Impact and Executive agents. Each workspace invokes a real backend action and exposes structured inputs, outputs, evidence and assumptions without exposing hidden chain-of-thought.

## Bugs discovered and rectified

### GitHub main did not show the final Nexus product

The final work initially existed on another branch and conflicting changes prevented an automatic merge. The repository was synchronized, conflicts were resolved, the product-first README and live links were merged to `main`, and CI was made authoritative.

### Localhost and Render links were confusing

The README did not clearly distinguish frontend, API and simulator services. Direct application and health links, local startup commands and Blueprint service names were documented. Render SPA rewriting was preserved so direct routes open correctly.

### CI failed after a documentation update

The failure was not safely ignored. Workflow logs showed validation fragility around the demo/Docker path. CI was corrected to use the deterministic E2E workflow and an explicit sandbox-build skip where appropriate. Later upgrades added authorization, route, secret, dependency and Docker checks.

### Human Approval link looked inactive

The sidebar used hash navigation and the approval action appeared disabled. Navigation was corrected, the decision status became a positive audit-locked badge, and the evidence export became a high-contrast action.

### Evidence export could be downloaded repeatedly

The export endpoint did not enforce one-time consumption. Backend policy now records `exported_at`, marks `export_status=consumed`, appends `evidence.exported`, returns HTTP 409 on reuse and keeps production execution false.

### Initial loading screen took too long

The application performed several sequential/eager requests while Render could be waking. A one-request bootstrap was introduced, the loading screen explained cold-start progress, and later the landing page was made independent of the API. Non-critical evidence, audit, agents and charts are now deferred.

### Explore Mode changed scenarios but not decisions

Tournament values were static constants. The tournament was rewritten so scores, risk, recovery, cost, verdicts, impact and executive wording derive from the selected controls and calculated counterfactuals. Four-preset regression tests prove distinct downstream outputs; the resilient case can recommend SAFE while baseline recommends OPTIMAL.

### Upload Operational JSON was difficult to identify

The file control looked secondary. It was redesigned as a high-contrast Import Operational JSON call-to-action with a larger icon, file-format cue, focus ring, hover state and responsive layout.

### Footer said approval was required after approval

The footer label was hardcoded. It now reads REQUIRED while awaiting review and RECORDED after a decision, with a regression test preventing contradictory labels.

### Approval had no role authorization

The old frontend used a fixed actor and the backend accepted any caller. Server-only access-code verification, secure comparison, short-lived HMAC tokens, persisted redacted fingerprints, mandatory rationale and authoritative role checks were added. Intern approval returns 403; Senior Developer approval succeeds only after all gates pass.

### Agent cards were not operational

Cards were audit-derived labels without workspaces. Eleven registered agents now have clickable routes, persisted execution records, real run/rerun calls, status, duration, hashes, errors, retries, evidence and audit-event views.

### Health and startup were unnecessarily slow

Startup synchronously seeded the legacy demo, and `/health` called an external simulator and discovered sandbox/provider state. Schema creation moved to lifespan, seeding became on-demand, health became process-local and readiness retained dependency checks. Local startup improved from 6.08 seconds to 2.57 seconds and health from 1.51 seconds to 123 ms.

## Safety outcome

Approval records a human decision and unlocks evidence export. It does not deploy, scale, reconfigure, roll back, call cloud APIs or execute commands. Interns cannot approve. The Verification Agent cannot approve. The model cannot approve. Only a verified human Senior Developer can record approval.

**PRODUCTION ACTION: NOT EXECUTED**

## What was learned

The most important lesson was that software credibility comes from behavior matching language. A button must perform a real backend action. A changed simulation must change its recommendation. A recorded approval must appear recorded everywhere. A security rule must be enforced by the backend, not merely shown in the UI. Human review of the running product exposed these gaps and converted an impressive demonstration into a more coherent software product.

