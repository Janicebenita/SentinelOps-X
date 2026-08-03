"""One-click SentinelOps storytelling video generator.

Captures deterministic application states, generates synchronized Indian-English
female narration, writes WebVTT-compatible SRT captions, and encodes H.264/AAC MP4.
No source tree or application state is modified beyond the seeded demo database.
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.util
import os
import shutil
import socket
import subprocess
import sys
import time
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "storytelling-output"
WIDTH, HEIGHT, FPS = 1920, 1080, 30
VOICE = "en-IN-NeerjaNeural"
RATE = "-5%"  # natural, measured delivery before final editorial retiming
FINAL_SPEED = 1.43
SCENE_SECONDS = 20
SECTION_TARGETS = (
    "command", "timeline", "evidence", "hypotheses", "twin", "replay",
    "tournament", "tournament", "counterfactual", "counterfactual", "blast",
    "evidence", "verification", "approval", "audit", "scorecard",
)

VISUALS = (
    """<div class='hero'><div><span class='badge ok'>HEALTHY</span><h1>Sentinel Shop Operations</h1><p>All customer journeys operating normally</p></div><div class='big ok'>100%<small>availability</small></div></div><div class='kpis'><article><small>ERROR RATE</small><b>0.00%</b></article><article><small>P95 LATENCY</small><b>84 ms</b></article><article><small>CHECKOUTS</small><b>1,284</b></article><article><small>DEPLOYMENT</small><b>NONE</b></article></div><div class='panel'><h2>Live service telemetry</h2><svg viewBox='0 0 1200 280'><polyline class='line' points='0,210 90,204 180,216 270,190 360,198 450,176 540,188 630,160 720,174 810,142 900,150 990,126 1080,134 1200,112'/></svg></div>""",
    """<div class='hero danger'><div><span class='badge bad'>SEV 1</span><h1>TN + SAVE10 checkout failed</h1><p>Customer-visible error detected and preserved for replay</p></div><div class='big bad'>500<small>HTTP response</small></div></div><div class='split'><div class='panel code'><h2>POST /checkout</h2><pre>{\n  "region": "TN",\n  "discount_code": "SAVE10",\n  "cart_value": 184.00\n}</pre></div><div class='panel'><h2>Error-rate spike</h2><svg viewBox='0 0 600 280'><polyline class='line badline' points='0,240 220,238 300,230 350,60 430,45 600,38'/></svg></div></div>""",
    """<h1>Evidence collection in progress</h1><p class='lead'>Independent signals arrive on the persisted incident timeline</p><div class='four'><article class='panel arrive'><span>01</span><h2>JSON Logs</h2><pre>TypeError: Decimal × None\nrequest_id=req-tn-1042</pre></article><article class='panel arrive d1'><span>02</span><h2>Metrics</h2><b class='metric bad'>8.7% errors</b><p>checkout route only</p></article><article class='panel arrive d2'><span>03</span><h2>Trace Span</h2><b>calculate_tax</b><p>regional_rate = null</p></article><article class='panel arrive d3'><span>04</span><h2>Git Evidence</h2><b>commit 074497c</b><p>TN configuration changed</p></article></div><div class='timeline'><i></i><b>incident.triggered</b><i></i><b>logs.collected</b><i></i><b>trace.correlated</b><i></i><b>evidence.persisted</b></div>""",
    """<h1>Ranked, falsifiable hypotheses</h1><p class='lead'>Confidence is a reasoned label—not guaranteed causality</p><div class='stack'><article class='panel winner'><div class='rank'>#1</div><div><h2>Nullable Tennessee tax rate</h2><p class='ok'>FOR · Trace shows Decimal × None · TN config is null</p><p class='bad'>AGAINST · Other regions succeed</p><small>Falsification: vary region and discount independently</small></div><b class='score'>HIGH</b></article><article class='panel'><div class='rank'>#2</div><div><h2>Discount calculation defect</h2><p>FOR · SAVE10 present in failing request</p><p>AGAINST · SAVE10 succeeds outside Tennessee</p></div><b class='score muted'>LOW</b></article></div>""",
    """<h1>Reliability Digital Twin</h1><p class='lead'>Immutable execution manifest shared by every candidate</p><div class='manifest panel'><article><small>TWIN ID</small><b>twin-1-6be81bca91</b></article><article><small>SOURCE COMMIT</small><b>074497caeaf3</b></article><article><small>RANDOM SEED</small><b>20260720</b></article><article><small>NETWORK</small><b class='bad'>DISABLED</b></article><article><small>CPU / MEMORY</small><b>1 CPU · 512 MB</b></article><article><small>LOCK HASH</small><b>91a7…3fd2</b></article></div><div class='hash panel'><small>MANIFEST SHA-256</small><b>6be81bca91c8f048…a0e4</b><span class='badge ok'>PERSISTED</span></div>""",
    """<h1>Deterministic incident replay</h1><p class='lead'>Same manifest · same seed · network disabled</p><div class='replays'><article class='panel pulse'><small>ATTEMPT 1</small><b class='bad'>HTTP 500</b><p>48 ms · hash 70c9…ff2a</p></article><article class='panel pulse d1'><small>ATTEMPT 2</small><b class='bad'>HTTP 500</b><p>48 ms · hash 70c9…ff2a</p></article><article class='panel pulse d2'><small>ATTEMPT 3</small><b class='bad'>HTTP 500</b><p>48 ms · hash 70c9…ff2a</p></article></div><div class='hero compact'><h2>REPRODUCIBILITY SCORE</h2><div class='big ok'>100%<small>3 identical reproductions</small></div></div>""",
    """<h1>Repair Tournament · three bounded candidates</h1><p class='lead'>Every patch runs inside an isolated copy of the same Twin</p><div class='three'><article class='panel'><span class='badge'>CANDIDATE A</span><h2>Local null fallback</h2><pre>rate or 0</pre><b class='metric'>84.2</b></article><article class='panel'><span class='badge'>CANDIDATE B</span><h2>Boundary validation</h2><pre>reject missing rate</pre><b class='metric'>78.6</b></article><article class='panel winner'><span class='badge ok'>CANDIDATE C</span><h2>Null-safe arithmetic</h2><pre>taxable × (rate or 0)</pre><b class='metric ok'>97.1</b></article></div><div class='safety'>ORIGINAL SOURCE TREE <b>UNCHANGED</b></div>""",
    """<h1>Deterministic verification gates</h1><p class='lead'>A mandatory failure blocks eligibility regardless of score</p><div class='gate panel'><div><b>GATE</b><b>A</b><b>B</b><b>C</b></div><div><span>Regression</span><i>✓</i><i>✓</i><i>✓</i></div><div><span>Unit + Integration</span><i>✓</i><i class='x'>×</i><i>✓</i></div><div><span>Ruff · MyPy · Bandit</span><i>✓</i><i>✓</i><i>✓</i></div><div><span>API Contract</span><i class='x'>×</i><i class='x'>×</i><i>✓</i></div><div><span>Replay Determinism</span><i>✓</i><i>✓</i><i>✓</i></div></div><div class='eligibility'><b class='bad'>A · DISQUALIFIED</b><b class='bad'>B · DISQUALIFIED</b><b class='ok'>C · ELIGIBLE</b></div>""",
    """<h1>Counterfactual Incident Simulator</h1><p class='lead'>Change nearby conditions and replay every candidate</p><div class='controls panel'><label>REGION <b>TN</b></label><label>DISCOUNT <b>SAVE10</b></label><label>TAX RATE <b>ABSENT</b></label><label>TRAFFIC <b>1 request</b></label></div><div class='matrix panel'><div><b>SCENARIO</b><b>ORIGINAL</b><b>A</b><b>B</b><b>C</b></div><div><span>TN + SAVE10</span><i class='x'>FAIL</i><i>PASS</i><i>PASS</i><i>PASS</i></div><div><span>GA + SAVE10</span><i>PASS</i><i>PASS</i><i>PASS</i><i>PASS</i></div><div><span>Slow dependency</span><i class='warn'>DEGRADED</i><i class='warn'>DEGRADED</i><i class='warn'>DEGRADED</i><i>PASS</i></div></div>""",
    """<h1>False fix detected</h1><p class='lead'>Candidate A passes the original regression—but breaks a nearby flow</p><div class='compare'><article class='panel'><small>ORIGINAL INCIDENT</small><h2>TN + SAVE10</h2><div class='result ok'>FIXED</div></article><div class='arrow'>→</div><article class='panel dangerbox'><small>COUNTERFACTUAL</small><h2>TN · no discount</h2><div class='result bad'>NEW FAILURE</div></article></div><div class='reject'><span>POLICY VERDICT</span><b>REJECT CANDIDATE A</b><p>False fix proven by scenario evidence IDs 18 and 23</p></div>""",
    """<h1>Estimated blast radius</h1><p class='lead'>Static dependencies, workflows, coverage and contracts</p><div class='blast'><article><b>POST /checkout</b><small>endpoint</small></article><i>→</i><article><b>calculate_tax</b><small>function</small></article><i>→</i><article><b>order total</b><small>workflow</small></article><i>←</i><article><b>regression</b><small>test</small></article></div><div class='three scores'><article class='panel'><b>A · 34/100</b><progress value='34' max='100'></progress></article><article class='panel dangerbox'><b>B · 68/100</b><progress value='68' max='100'></progress></article><article class='panel winner'><b>C · 18/100</b><progress value='18' max='100'></progress></article></div><p class='disclaimer'>Transparent estimate · not certainty</p>""",
    """<h1>Causal Evidence Graph</h1><p class='lead'>Every important claim links back to collected evidence</p><div class='egraph'><article><small>SYMPTOM</small><b>HTTP 500</b></article><i>→</i><article><small>LOG + TRACE</small><b>Decimal × None</b></article><i>→</i><article><small>SOURCE</small><b>Nullable TN rate</b></article><i>→</i><article><small>REPLAY</small><b>3 identical failures</b></article><i>→</i><article class='winner'><small>DECISION</small><b>Candidate C</b></article></div><div class='panel evidence'><b>CLAIM COMPLETENESS</b><strong>100%</strong><p>Logs · Metrics · Traces · Git · Tests · Policy</p></div>""",
    """<h1>Adversarial patch review</h1><p class='lead'>The reviewer challenges each candidate; it cannot generate or approve a patch</p><div class='split'><div class='panel'><h2>ADVOCATE CASE</h2><p>Minimal one-line repair</p><p>Preserves public contract</p><p>All mandatory gates pass</p></div><div class='panel dangerbox'><h2>RED-TEAM CHALLENGES</h2><p>Does it mask the symptom?</p><p>Does it weaken validation?</p><p>Does it fail under nearby inputs?</p><p>Does it touch protected paths?</p></div></div><div class='verdict'><span>DETERMINISTIC VERDICT</span><b class='ok'>CANDIDATE C ELIGIBLE</b></div>""",
    """<h1>Human approval checkpoint</h1><p class='lead'>The agent has stopped. It cannot approve its own repair.</p><div class='approval panel'><div class='shield'>✓</div><div><h2>Candidate C ready for review</h2><p>All mandatory gates passed · blast radius 18/100</p><div class='buttons'><button>REJECT</button><button class='approve'>APPROVE REPAIR</button></div></div></div><div class='safety-grid'><b>ORIGINAL SOURCE CHANGED <span>NO</span></b><b>AUTOMATIC DEPLOYMENT <span>NO</span></b><b>HUMAN APPROVAL REQUIRED <span>YES</span></b></div>""",
    """<h1>Tamper-evident incident package</h1><p class='lead'>Approval recorded · PR report created · nothing deployed</p><div class='hashes'><article class='panel'><small>FIRST EVENT HASH</small><b>12fa9c…8e41</b></article><article class='panel'><small>FINAL AUDIT-CHAIN HASH</small><b>e8c410…117a</b></article><article class='panel'><small>PACKAGE HASH</small><b>1dd201…b9ce</b></article></div><div class='hero compact'><span class='badge ok'>✓ VERIFIED</span><h2>JSON · Executive report · ZIP evidence bundle</h2><p>Tamper-evident audit chain—not blockchain or formal proof</p></div>""",
    """<h1>Reliability engineering scorecard</h1><p class='lead'>Computed from persisted workflow events</p><div class='scorecards'><article><small>CLAIMS LINKED</small><b>100%</b></article><article><small>CANDIDATES</small><b>3</b></article><article><small>SCENARIOS</small><b>8</b></article><article><small>FALSE FIXES</small><b>2</b></article><article><small>POLICY BLOCKS</small><b>2</b></article><article><small>SOURCE MUTATIONS</small><b class='ok'>0</b></article><article><small>AUTO DEPLOYMENTS</small><b class='ok'>0</b></article><article><small>APPROVALS BYPASSED</small><b class='ok'>0</b></article></div><div class='closing'>Evidence-proven · Human-controlled · Nothing automatically deployed</div>""",
    """<div class='finale-card'><div class='finale-shield'>✓</div><h1>Evidence-proven reliability engineering</h1><p>Deterministic checks before confidence</p><p>Human approval before repository action</p><p>Nothing automatically deployed</p><div class='thank-you'>THANK YOU</div><small>SENTINELOPS · AUTONOMOUS AI RELIABILITY ENGINEER</small></div>""",
)

STORY_SHELL = """<!doctype html><html><head><style>
*{box-sizing:border-box}body{margin:0;background:#061119;color:#e8f7f5;font-family:Segoe UI,Arial,sans-serif;overflow:hidden}.shell{height:1080px;padding:58px 78px;background:radial-gradient(circle at 80% 0,#0b3440,transparent 38%),linear-gradient(135deg,#061119,#071c25)}header{height:76px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #1b4550}.brand{font-size:25px;font-weight:800;letter-spacing:3px}.brand span,.ok{color:#36dfbd}.mode{color:#80aeb5;font-size:15px;letter-spacing:2px}#stage{height:850px;padding:46px 5px;animation:enter .65s ease}h1{font-size:46px;margin:0 0 8px}h2{margin:6px 0 14px}.lead{font-size:21px;color:#91b8be;margin:0 0 34px}.hero{display:flex;justify-content:space-between;align-items:center;padding:42px;border:1px solid #1f6471;background:#092732;border-radius:18px;margin-bottom:28px}.hero.danger{border-color:#a83f59;background:#291624}.hero.compact{padding:30px;margin-top:26px}.big{font-size:62px;font-weight:900}.big small{display:block;font-size:15px;color:#8cb4ba}.bad{color:#ff607f}.badge{display:inline-block;padding:8px 14px;border:1px solid #317080;border-radius:18px;font-size:13px;letter-spacing:1px}.badge.ok{border-color:#28a88d}.badge.bad{border-color:#c64564}.kpis,.four,.three,.hashes,.scorecards{display:grid;grid-template-columns:repeat(4,1fr);gap:20px;margin-bottom:26px}.kpis article,.scorecards article{padding:25px;background:#0a2029;border:1px solid #1b4650;border-radius:12px}.kpis b,.scorecards b{display:block;font-size:31px;margin-top:8px}.panel{background:#091f28;border:1px solid #1c4854;border-radius:14px;padding:28px}.split{display:grid;grid-template-columns:1fr 1fr;gap:25px}.code pre,pre{color:#8debd8;font:19px Consolas;line-height:1.6}.line{fill:none;stroke:#33dfbd;stroke-width:7;stroke-linecap:round;stroke-dasharray:1800;animation:draw 4s ease forwards}.badline{stroke:#ff607f}.four article{min-height:220px}.four span,.rank{font-size:30px;color:#37dfbd}.metric{font-size:36px}.timeline{display:flex;align-items:center;justify-content:space-around;padding:30px;background:#081a22}.timeline i{width:14px;height:14px;background:#35ddb9;border-radius:50%;box-shadow:0 0 18px #35ddb9}.arrive{animation:rise .7s both}.d1{animation-delay:.35s}.d2{animation-delay:.7s}.d3{animation-delay:1.05s}.stack{display:grid;gap:22px}.stack article{display:grid;grid-template-columns:90px 1fr 100px;align-items:center}.winner{border-color:#31d8b5!important;box-shadow:0 0 24px #1f806855}.score{align-self:start}.muted{color:#79989e}.manifest{display:grid;grid-template-columns:repeat(3,1fr);gap:30px}.manifest article b{display:block;margin-top:8px;font-size:20px}.hash{margin-top:24px;display:flex;gap:35px;align-items:center}.replays{display:grid;grid-template-columns:repeat(3,1fr);gap:24px}.replays b{display:block;font-size:35px;margin:20px 0}.pulse{animation:pulse 1.4s ease}.three{grid-template-columns:repeat(3,1fr)}.three article{min-height:260px}.safety,.closing{text-align:center;padding:25px;border:1px solid #2a9a83;background:#0b302f;font-size:20px}.gate>div,.matrix>div{display:grid;grid-template-columns:2fr repeat(3,1fr);padding:12px;border-bottom:1px solid #173a44}.gate i,.matrix i{color:#36dfbd;font-style:normal;font-weight:800}.gate .x,.matrix .x{color:#ff607f}.eligibility{display:flex;justify-content:space-around;margin-top:25px}.controls{display:flex;justify-content:space-around;margin-bottom:25px}.controls label{color:#83aeb4}.controls b{display:block;color:white;font-size:24px;margin-top:8px}.matrix>div{grid-template-columns:2fr repeat(4,1fr)}.warn{color:#ffc85c!important}.compare{display:grid;grid-template-columns:1fr 100px 1fr;align-items:center}.arrow{text-align:center;font-size:60px}.result{font-size:45px;font-weight:900;margin-top:30px}.dangerbox{border-color:#a83f59!important}.reject,.verdict{text-align:center;margin-top:30px;padding:28px;background:#321722;border:1px solid #c84664}.reject b,.verdict b{display:block;font-size:30px}.blast,.egraph{display:flex;align-items:center;justify-content:space-between;margin:55px 0}.blast article,.egraph article{padding:28px;border:1px solid #277487;background:#0a2630;border-radius:12px;text-align:center}.blast i,.egraph i{font-size:40px;color:#32dcba}.blast small,.egraph small{display:block;color:#85aeb4}.scores article{min-height:auto}.scores progress{width:100%;height:22px}.disclaimer{text-align:center;color:#8eb4ba}.evidence{display:flex;align-items:center;justify-content:space-between}.evidence strong{font-size:50px;color:#35dfbd}.approval{display:flex;align-items:center;gap:45px}.shield{width:130px;height:130px;border:3px solid #35dfbd;border-radius:50%;display:grid;place-items:center;font-size:70px;color:#35dfbd}.buttons{display:flex;gap:20px;margin-top:25px}button{padding:15px 30px;background:#152b34;color:white;border:1px solid #55747a;border-radius:8px}.approve{background:#198d77}.safety-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:24px}.safety-grid b{padding:20px;background:#092a2c}.safety-grid span{color:#36dfbd}.hashes{grid-template-columns:repeat(3,1fr)}.hashes b{display:block;font-size:21px;margin-top:14px}.scorecards{grid-template-columns:repeat(4,1fr)}.scorecards article{text-align:center}.closing{font-size:28px;margin-top:28px}@keyframes enter{from{opacity:0;transform:translateY(30px)}to{opacity:1;transform:none}}@keyframes rise{from{opacity:0;transform:translateY(35px)}to{opacity:1;transform:none}}@keyframes draw{from{stroke-dashoffset:1800}to{stroke-dashoffset:0}}@keyframes pulse{50%{box-shadow:0 0 35px #ff607f66}}
</style><style>.finale-card{text-align:center;padding:55px}.finale-shield{margin:0 auto 25px;width:130px;height:130px;border:3px solid #36dfbd;border-radius:50%;display:grid;place-items:center;color:#36dfbd;font-size:70px}.finale-card p{font-size:24px;color:#9cc3c7}.thank-you{font-size:72px;font-weight:900;color:#36dfbd;letter-spacing:10px;margin:45px 0 20px;text-shadow:0 0 30px #36dfbd55}</style></head><body><div class='shell'><header><div class='brand'>SENTINEL<span>OPS</span></div><div class='mode'>RELIABILITY DIGITAL TWIN · SIMULATED INCIDENT RUN</div></header><main id='stage'></main></div></body></html>"""


@dataclass(frozen=True)
class Scene:
    state: str
    title: str
    narration: str


SCENES = (
    Scene("top", "Meet SentinelOps Nexus", "Welcome to SentinelOps Nexus, the Enterprise Operational Digital Twin. This demonstration begins before a customer-visible incident. The Payment Service is healthy now, whilst traffic and Redis memory pressure are rising. Nexus asks which constraint will become the next bottleneck, when customers could feel it, and which intervention remains safe under nearby failure conditions. Every figure in this command centre comes from a persisted deterministic workflow."),
    Scene("time-travel", "Yesterday, now and tomorrow", "The time-travel view connects yesterday's baseline, the present state, and the next forty-five minutes. Redis safe capacity is forecast to cross in thirty minutes. The customer-impact estimate follows at forty-five minutes, before the conventional reactive alert becomes active. Operators can inspect memory, checkout latency, queue depth and alert state at each point, making the early-warning claim visible rather than hidden inside a model."),
    Scene("forecast", "A transparent forecast", "This forecast is deliberately bounded and inspectable. Nexus displays the linear saturation equation, the ninety per cent safe-capacity threshold, residual mean absolute error, and a plus-or-minus time bound. Its confidence label is a heuristic evidence score, not a calibrated probability. The assumptions remain beside the result, so a reviewer can challenge capacity, workload shape, or telemetry quality before accepting the recommendation."),
    Scene("evidence", "Evidence before confidence", "Material claims cite persisted, content-hashed evidence. Configuration establishes capacity and replicas; metrics establish the memory slope and queue growth; trace-like events link Redis to the Payment Service critical path. The agent activity trace shows structured outputs and evidence references, never hidden chain of thought. This creates a reviewable path from raw observation, through forecast, to the executive finding."),
    Scene("twin", "Explore the Digital Twin", "Explore Mode turns the demonstration into a working lab. Change traffic from half to ten times baseline, Redis capacity, application replicas, and dependency latency. Presets provide baseline, ten-times traffic, constrained, and resilient conditions. Rerunning creates a new persisted bounded Twin with the same documented method. It is simulation only: no infrastructure command, deployment, or production mutation is available from this control."),
    Scene("scenarios", "Twelve deterministic futures", "Each Twin is replayed through twelve deterministic scenarios: baseline growth, Redis crash and latency, replica failover, ten-times traffic, million-user stress, reduced capacity, increased replicas, rollback, rate limiting, cache-policy correction, and configuration drift. Select any row to inspect its inputs, recovery time, result hash and whether the bottleneck was avoided. The common seed and manifest make comparisons repeatable."),
    Scene("tournament", "The Intervention Tournament", "Nexus compares three intervention strategies. FAST scales application replicas immediately. SAFE adds Redis capacity with controlled failover and traffic shaping. OPTIMAL combines Redis capacity, cache-policy correction, and gradual scaling. Every candidate is scored for safety, recovery, risk and estimated cost, but the decisive rule is simple: eligibility overrides score. A failed mandatory gate can never be outweighed by apparent confidence."),
    Scene("tournament", "Rejecting the plausible false fix", "FAST is attractive because it is quick and inexpensive. Yet the bottleneck sits in Redis, and the mandatory failover test fails. Nexus therefore disqualifies FAST regardless of its numerical score. SAFE remains an eligible lower-cost alternative, whilst OPTIMAL wins under the transparent weighting. This is the core value of the Twin: test a plausible intervention against adverse conditions before customers become the experiment."),
    Scene("impact", "Business impact with visible assumptions", "The operational forecast is translated into an estimated business exposure using displayed inputs: request rate, conversion rate, average order value, the risk window, projected failure rate and an SLA penalty. The result is not an accounting fact or guaranteed loss. It is an operational estimate designed to help a human compare urgency, intervention cost and uncertainty with the arithmetic in plain sight."),
    Scene("approval", "Human approval remains mandatory", "Nexus now stops at the Human Approval Gateway. The recommended action, evidence and contradictory evidence are ready for an accountable reviewer. Guided Demo never presses approve. Even an explicit approval only records the named decision, appends the tamper-evident audit timeline, and enables evidence export. It does not deploy, change Redis, scale replicas, or call a production control plane. Production action is not executed."),
    Scene("audit", "A tamper-evident decision record", "The audit timeline chains each persisted event with SHA two-fifty-six. The export package contains the incident, Twin manifest, forecast, scenarios, tournament, verification, business impact, executive brief, evidence and human decision, with a checksum manifest. This supports tamper detection and repeatable review. It is not blockchain, legal non-repudiation, or a claim that the bounded Twin perfectly reproduces production."),
    Scene("top", "Predict, test, and decide safely", "SentinelOps Nexus turns late reactive alerting into an earlier, evidence-backed decision. It predicts the emerging Redis bottleneck, tests interventions across deterministic futures, rejects a convincing false fix, quantifies estimated exposure, and preserves human authority at the final boundary. Explore every input, rerun every scenario, and inspect every hash. Throughout this demonstration, and by design, production action remains not executed."),
)


def stamp(seconds: int) -> str:
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},000"


def run(command: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None) -> None:
    subprocess.run(command, cwd=cwd, env=env, check=True)


def install_dependencies() -> None:
    run([sys.executable, "-m", "pip", "install", "-e", ".[storytelling]"])
    run([sys.executable, "-m", "playwright", "install", "chromium"])


def require_dependencies() -> None:
    missing = [name for name in ("edge_tts", "playwright", "PIL", "imageio_ffmpeg") if importlib.util.find_spec(name) is None]
    if missing:
        raise SystemExit(f"Missing fixed storytelling dependencies: {', '.join(missing)}. Run this script once with --install.")


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for(url: str, timeout: int = 45) -> None:
    import urllib.request
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status < 500:
                    return
        except OSError:
            time.sleep(.4)
    raise RuntimeError(f"Service failed to start: {url}")


def start_services() -> tuple[list[subprocess.Popen[bytes]], str]:
    api_port = free_port()
    ui_port = free_port()
    pnpm = shutil.which("pnpm.cmd") or shutil.which("pnpm")
    if not pnpm:
        raise RuntimeError("pnpm is required to run the frontend")
    api = [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", str(api_port)]
    ui = [pnpm, "dev", "--port", str(ui_port)]
    api_env = dict(os.environ, CORS_ORIGINS=f"http://127.0.0.1:{ui_port}")
    ui_env = dict(os.environ, VITE_API_BASE_URL=f"http://127.0.0.1:{api_port}")
    processes = [
        subprocess.Popen(api, cwd=ROOT, env=api_env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT),
        subprocess.Popen(ui, cwd=ROOT / "frontend", env=ui_env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT),
    ]
    wait_for(f"http://127.0.0.1:{api_port}/health")
    wait_for(f"http://127.0.0.1:{ui_port}")
    return processes, f"http://127.0.0.1:{ui_port}"


async def capture(url: str, durations: list[float]) -> Path:
    from playwright.async_api import async_playwright
    recordings = OUT / "recordings"
    recordings.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as manager:
        browser = await manager.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": WIDTH, "height": HEIGHT},
            device_scale_factor=1,
            record_video_dir=str(recordings),
            record_video_size={"width": WIDTH, "height": HEIGHT},
        )
        await context.add_init_script("""
          (() => {
            const install = () => {
              const cursor = document.createElement('div');
              cursor.id = 'story-cursor';
              Object.assign(cursor.style, {
                position:'fixed', width:'30px', height:'30px', border:'4px solid #ffd43b',
                borderRadius:'50%', background:'rgba(255,212,59,.18)', zIndex:'2147483647',
                pointerEvents:'none', transform:'translate(-50%,-50%)', transition:'transform .12s ease'
              });
              document.body.appendChild(cursor);
              addEventListener('mousemove', e => {
                cursor.style.left = e.clientX + 'px'; cursor.style.top = e.clientY + 'px';
              });
              addEventListener('mousedown', () => cursor.style.transform='translate(-50%,-50%) scale(.65)');
              addEventListener('mouseup', () => cursor.style.transform='translate(-50%,-50%) scale(1)');
              document.documentElement.style.scrollBehavior='smooth';
            };
            document.readyState === 'loading' ? addEventListener('DOMContentLoaded', install) : install();
          })();
        """)
        page = await context.new_page()
        await page.goto(url, wait_until="networkidle", timeout=90000)
        await page.get_by_role("heading", name="Predict tomorrow's bottleneck before customers experience it.").wait_for()
        for index, scene in enumerate(SCENES):
            scene_started = time.monotonic()
            if index == 0:
                await page.get_by_role("button", name="One-click Guided Demo").click()
            scroll_target = page.locator("body") if scene.state == "top" else page.locator(f"#{scene.state}")
            await scroll_target.evaluate("node => node.scrollIntoView({behavior:'smooth', block:'center'})")
            await page.mouse.move(250 + (index % 3) * 180, 190, steps=30)
            await page.wait_for_timeout(3000)
            for x, y in ((620, 430), (1240, 620), (1570, 300)):
                await page.mouse.move(x, y, steps=55)
                await page.wait_for_timeout(2300)
            remaining_ms = int((durations[index] - (time.monotonic() - scene_started)) * 1000)
            await page.wait_for_timeout(max(100, remaining_ms))
        video = page.video
        if video is None:
            raise RuntimeError("Playwright did not create the requested browser recording")
        await page.close()
        raw_path = Path(await video.path())
        await context.close()
        await browser.close()
    recording_target = OUT / "browser-session.webm"
    shutil.copy2(raw_path, recording_target)
    return recording_target


async def narrate() -> None:
    import edge_tts
    audio = OUT / "segments"
    audio.mkdir(parents=True, exist_ok=True)
    for index, scene in enumerate(SCENES):
        target = audio / f"{index:02d}.mp3"
        if target.exists() and target.stat().st_size > 1024:
            continue
        communicate = edge_tts.Communicate(scene.narration, VOICE, rate=RATE)
        await communicate.save(str(target))


def audio_durations() -> list[float]:
    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    measured: list[float] = []
    for index in range(len(SCENES)):
        result = subprocess.run(
            [ffmpeg, "-hide_banner", "-i", str(OUT / "segments" / f"{index:02d}.mp3")],
            capture_output=True, text=True, check=False,
        )
        match = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", result.stderr)
        if not match:
            raise RuntimeError(f"Could not measure narration segment {index}")
        hours, minutes, seconds = match.groups()
        measured.append(int(hours) * 3600 + int(minutes) * 60 + float(seconds))
    return measured


def scene_durations() -> list[float]:
    """Keep each visual visible through its narration, with a 750 ms breathing gap."""
    return [max(float(SCENE_SECONDS), duration + .75) for duration in audio_durations()]


def write_srt(durations: list[float]) -> Path:
    target = ROOT / "demo_storytelling_video.srt"
    blocks = []
    elapsed = 0.0
    for index, scene in enumerate(SCENES):
        start, end = elapsed / FINAL_SPEED, (elapsed + durations[index]) / FINAL_SPEED
        blocks.append(f"{index + 1}\n{stamp(round(start))} --> {stamp(round(end))}\n{scene.title}\n{scene.narration}\n")
        elapsed += durations[index]
    target.write_text("\n".join(blocks), encoding="utf-8")
    return target


def encode(durations: list[float], recording: Path | None = None) -> tuple[Path, Path]:
    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    inputs: list[str] = []
    filters: list[str] = []
    elapsed = 0.0
    for index in range(len(SCENES)):
        inputs.extend(("-i", str(OUT / "segments" / f"{index:02d}.mp3")))
        delay = round(elapsed * 1000)
        filters.append(f"[{index}:a]loudnorm=I=-16:LRA=5:TP=-1.5,adelay={delay}|{delay}[a{index}]")
        elapsed += durations[index]
    joined = "".join(f"[a{index}]" for index in range(len(SCENES)))
    total = elapsed
    final_total = total / FINAL_SPEED
    fade_start = max(0.0, total - 2.0)
    filters.append(f"{joined}amix=inputs={len(SCENES)}:duration=longest:dropout_transition=0,alimiter=limit=0.9,apad=whole_dur={total},afade=t=out:st={fade_start}:d=2[voice]")
    voice = ROOT / "voice.wav"
    run([ffmpeg, "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filters), "-map", "[voice]", "-t", str(total), "-ar", "48000", "-ac", "2", str(voice)])
    video = ROOT / "demo_storytelling_video.mp4"
    recording = recording or OUT / "browser-session.webm"
    if not recording.exists():
        raise RuntimeError("Dynamic browser recording is missing; run the complete generator.")
    run([ffmpeg, "-y", "-loglevel", "error", "-i", str(recording), "-i", str(voice), "-t", str(final_total), "-filter_complex", f"[0:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2,format=yuv420p,setpts=PTS/{FINAL_SPEED},fade=t=out:st={max(0, final_total-2)}:d=2[v];[1:a]atempo={FINAL_SPEED}[a]", "-map", "[v]", "-map", "[a]", "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(video)])
    return video, voice


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install", action="store_true", help="Install the fixed storytelling dependencies first")
    args = parser.parse_args()
    if args.install:
        install_dependencies()
    require_dependencies()
    OUT.mkdir(exist_ok=True)
    processes: list[subprocess.Popen[bytes]] = []
    try:
        processes, url = start_services()
        asyncio.run(narrate())
        durations = scene_durations()
        recording = asyncio.run(capture(url, durations))
        srt = write_srt(durations)
        video, voice = encode(durations, recording)
        print(f"Generated:\n  {video}\n  {srt}\n  {voice}")
        return 0
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()


if __name__ == "__main__":
    raise SystemExit(main())
