# Defensive Agent Evaluation: Code Architecture

## Goals and non-goals

Build a reproducible, provider-neutral evaluation system that detects agent reliability failures without introducing hidden behavior into production systems. The first implementation is deliberately synthetic and standard-library-only. It validates the evaluator design, not the safety of any real model.

Non-goals: backdoor training, reward-model modification, authentication bypass, production credentials, unapproved network access, or claiming real-agent results from fixture tests.

## System boundaries

```text
                 trusted experiment configuration
                              |
                              v
                    [Scenario / Task Registry]
                              |
                              v
                    [Evaluation Orchestrator]
                     /         |          \
                    v          v           v
             [Agent Adapter] [Tool Adapter] [Harness Adapter]
                    |          |           |
                    +----------+-----------+
                               |
                         execution events
                               |
                 +-------------+-------------+
                 |                           |
                 v                           v
       [Evidence / Event Ledger]     [Candidate Report]
                 |                           |
                 v                           |
        [Independent Verifier] <--------------+
                 |
                 v
         [Metrics Aggregator]
                 |
                 v
       [JSONL events + JSON reports]
                 |
                 v
        [Regression tests / CI]
```

The candidate report is an input to the verifier, never an authority. Only the evaluator-owned event ledger, run identity, allowlisted tool results, and independently checked postconditions can establish success.

## Package layout

```text
research/
  ARCHITECTURE.md             # this design and trust boundaries
  THREAT_MODEL.md             # threats, assets, assumptions
  EXPERIMENT_PROTOCOL.md      # repeatable execution protocol
  REMEDIATION_REPORT.md       # findings and remediation status
  rlvr_eval.py                # synthetic verifier reference implementation
  harness_fidelity.py         # synthetic long-horizon/state-retention fixtures
  schemas/
    scenario.schema.json      # scenario input contract (future)
    result.schema.json        # result contract (future)
results/
  baseline.json               # generated fixture results; real experiments NOT RUN
  adversarial_evaluation.json # generated fixture results; real experiments NOT RUN
tests/
  test_verifier_integrity.py
  test_harness_fidelity.py
.github/workflows/ci.yml      # deterministic tests and artifact upload
```

The schema files are planned interfaces, not represented as implemented until they are added and validated. Avoid duplicate artifacts if the repository already gains equivalent schemas elsewhere.

## Core interfaces

### Scenario

A scenario should be immutable once a run starts and contain:
- `scenario_id`, version, task category, and expected postconditions
- trusted instructions and separate untrusted fixture content
- allowed tools, timeouts, retry limits, and environment isolation level
- clean/adversarial condition and synthetic trigger identifier, if applicable
- evaluator version and deterministic seed

Never put credentials in scenario JSON. Use opaque references to isolated test fixtures where a future authorized adapter needs secrets.

### AgentAdapter

A provider-specific adapter receives a task and returns a candidate response plus requested tool actions. It must not receive evaluator secrets, hidden expected answers, or the verifier's internal state. Adapters are optional; the current code has no live agent adapter.

### ToolAdapter

Every tool call should yield a structured event with a unique event ID, run ID, tool name, allowlist decision, start/end timestamps, exit/result status, timeout state, and a redacted output reference. Default policy is deny. Production/network-capable adapters remain disabled unless separately authorized.

### Event ledger

Append-only evaluator-owned records form the audit trail. Every record includes a unique run ID, monotonic sequence number, event type, source identity, timestamp, and content hash. Candidate-authored text is tagged untrusted. Replay checks bind evidence to the current run and event ID. Do not store secrets or unredacted sensitive output.

### Independent verifier

The verifier consumes expected postconditions and trusted ledger observations. It checks task-specific facts rather than trusting prose, exit code alone, or a candidate-generated screenshot/log. For health checks, distinguish DNS/TCP reachability, TLS, authentication, application health, and the requested operation's postcondition. Missing evidence is a failure or inconclusive result, never implicit success.

### Metrics

Report numerator and denominator, not only percentages:
- independently verified task success
- false-success and false-negative claims
- instruction-boundary violations
- unauthorized tool attempts
- replay/mismatched-run evidence
- verifier disagreements, timeouts, missing evidence
- state-retention failures and recovery after compaction
- input/output token counts where the provider exposes them

Keep synthetic fixture metrics separate from real model/agent metrics.

### Result record

Each experiment result should include schema version, run ID, UTC timestamps, repository commit, scenario hash, evaluator version, adapter/provider/model version (or NOT RUN), configuration hash, raw-event artifact reference, aggregate metrics, limitations, and explicit status: PASS, FAIL, INCONCLUSIVE, or NOT RUN.

## Execution lifecycle

1. Validate configuration and reject secrets, unsafe targets, and unapproved tools.
2. Freeze scenario, verifier, and adapter versions.
3. Create a unique run ID and isolated workspace.
4. Execute clean and adversarial variants with matched task semantics.
5. Capture tool events in the evaluator-owned ledger.
6. Verify postconditions independently from candidate claims.
7. Aggregate metrics and disagreement records.
8. Persist redacted inputs, outputs, configs, and hashes.
9. Re-run confirmed failures as regression tests.
10. Mark real-agent experiments NOT RUN unless the adapter actually executed and evidence is present.

## Harness fidelity and state retention

The synthetic harness-fidelity fixture models a common failure mode: rolling history truncation can remove earlier constraints or observations. Compare a truncation policy with a state-preserving policy on the same synthetic event sequence. The fixture only checks deterministic retention behavior; it does not reproduce a provider's hidden reasoning or prove that compaction improves model accuracy.

For a future provider experiment, use only supported API state-management features, keep task and tool outcomes identical between arms, record context sizes and compaction events, and score final outcomes with the same independent verifier. Never claim access to private chain-of-thought. Evaluate observable actions, retained facts, and outcomes.

## Security controls

- Synthetic fixtures by default; live adapters opt-in and disabled by default.
- Explicit tool allowlist, least privilege, per-run isolation, bounded timeouts.
- Untrusted tool output is data, not policy.
- No candidate control over expected outcomes, evidence ledger, scoring code, or result files.
- Pin versions and hash datasets/configuration.
- Redact secrets before logs or artifact upload.
- Require human approval for production-impacting actions.
- Preserve original project state; use a dedicated branch and reviewable PR.
- Fail closed on missing, malformed, stale, or cross-run evidence.

## Rollout plan

**Phase 1, current:** synthetic verifier and harness-fidelity fixtures, unit tests, CI artifacts.

**Phase 2:** schema validation, signed/hash-chained event records, scenario registry, repeat runner and statistical summaries.

**Phase 3:** mock adapters for coding/research/SSH-diagnosis/API-health tasks in a disposable sandbox.

**Phase 4:** authorized model/provider adapters with matched clean/adversarial runs, explicit cost/latency budgets, and independent scoring.

**Phase 5:** integration into CATCH-style verification only after mapping the real verifier interface and adding shadow-mode comparison. Never silently change production reward or verifier rules.

## Acceptance gates

- All synthetic regression tests pass reproducibly.
- Evidence replay and candidate forgery cannot change verdicts.
- Candidate claims are distinct from verified outcomes.
- Reports distinguish synthetic fixtures from real-agent experiments.
- CI stores generated artifacts and reports failures accurately.
- Real-agent work remains NOT RUN until evidence-backed execution occurs.
