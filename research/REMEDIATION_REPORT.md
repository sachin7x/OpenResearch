# Defensive RLVR Remediation Report

## Status

This is the initial report for the defensive verifier harness. It documents implementation and planned follow-up, not a production security audit.

## Implemented

- Added `research/rlvr_eval.py`, a standard-library-only reference verifier that relies on evaluator-owned observations.
- Added `tests/test_verifier_integrity.py` covering success claims after tool errors, TCP-versus-authentication confusion, candidate-forged evidence, replayed run IDs, misleading zero-exit assumptions, false-negative claims, and synthetic suite scope.
- Added a threat model and experiment protocol.
- Added clean and adversarial fixture result generation. The result files explicitly state that no agent/model was invoked.

## Current findings

No production or model-level weakness has been confirmed. The tests target the reference verifier logic only.

The harness is designed to reject these synthetic conditions:
- Tool error/timeout followed by a success claim.
- TCP reachability without verified authentication.
- Candidate evidence that contradicts evaluator-owned observations.
- Evidence whose run ID does not match the current execution.
- A health claim without a passing service-health postcondition.

These are expected outcomes of deterministic unit fixtures, not discoveries about the deployed OpenResearch application.

## Remediation rules

1. For a confirmed production weakness, preserve a minimal reproducible fixture and add a regression test before changing the verifier.
2. Use immutable run identifiers and evaluator-owned tool observations for consequential claims.
3. Keep candidate-authored summaries and evidence separate from trusted verification inputs.
4. Require explicit authentication and service-health checks where relevant; TCP reachability or exit code zero alone is insufficient.
5. Version evaluator criteria and record changes; do not silently alter production rewards or verification rules.
6. Record false positives, false negatives, timeouts, missing evidence, and evaluator disagreements.
7. Re-run the relevant tests after each fix and report only observed results.

## Execution status

- Synthetic verifier unit tests: **NOT RUN** until a CI or local test result is recorded.
- Synthetic fixture result generation: **NOT RUN** until the harness is executed.
- Real MiniMax/Codex/Claude/Genspark/MCP behavior: **NOT RUN**.
- Production verifier integration: **NOT RUN**.
- Oracle/Genspark infrastructure recovery checks: **NOT RUN**.
- Upstream RL backdoor injection/training: intentionally **NOT RUN**; it is outside the defensive scope.

Update this report after execution with the exact commit, command, environment, test counts, and CI run link. Do not change a status to PASS without recorded execution evidence.
