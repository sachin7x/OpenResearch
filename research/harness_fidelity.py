"""Synthetic harness-fidelity fixtures for long-horizon state retention.

This module compares two deterministic history policies. It does not call a
model/provider, inspect private reasoning, or claim that summarization improves
real agent performance. It only tests whether required observable facts survive
a deliberately constrained history representation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass(frozen=True)
class Event:
    sequence: int
    kind: str
    fact_key: str
    fact_value: str


@dataclass(frozen=True)
class RetentionResult:
    policy: str
    retained_event_sequences: list[int]
    retained_facts: dict[str, str]
    required_facts: dict[str, str]
    missing_facts: list[str]
    passed: bool


def rolling_truncation(events: Iterable[Event], max_events: int) -> list[Event]:
    """Retain only the newest max_events entries, mirroring a simple rolling window."""
    if max_events < 0:
        raise ValueError("max_events must be >= 0")
    ordered = sorted(events, key=lambda event: event.sequence)
    return ordered[-max_events:] if max_events else []


def state_preserving_compaction(events: Iterable[Event]) -> list[Event]:
    """Keep the latest event for each fact key, ordered by its original sequence.

    This is a deterministic synthetic policy, not an LLM summarizer. In a real
    harness, any generated summary must be checked against source events.
    """
    latest: dict[str, Event] = {}
    for event in sorted(events, key=lambda item: item.sequence):
        latest[event.fact_key] = event
    return sorted(latest.values(), key=lambda item: item.sequence)


def score_retention(
    policy: str, retained: Iterable[Event], required_facts: dict[str, str]
) -> RetentionResult:
    retained_events = list(retained)
    facts = {event.fact_key: event.fact_value for event in retained_events}
    missing = sorted(
        key for key, expected in required_facts.items() if facts.get(key) != expected
    )
    return RetentionResult(
        policy=policy,
        retained_event_sequences=[event.sequence for event in retained_events],
        retained_facts=facts,
        required_facts=dict(required_facts),
        missing_facts=missing,
        passed=not missing,
    )


def build_fixture() -> dict:
    """Run paired policies over a fixed synthetic long-horizon task."""
    events = [
        Event(1, "constraint", "must_not_use_network", "true"),
        Event(2, "observation", "service_tcp", "reachable"),
        Event(3, "tool_result", "auth_status", "denied"),
        Event(4, "instruction", "reporting_rule", "do_not_claim_success_without_auth"),
        Event(5, "noise", "intermediate_note", "synthetic filler A"),
        Event(6, "noise", "intermediate_note_2", "synthetic filler B"),
        Event(7, "final_observation", "service_health", "unverified"),
    ]
    required = {
        "must_not_use_network": "true",
        "auth_status": "denied",
        "reporting_rule": "do_not_claim_success_without_auth",
        "service_health": "unverified",
    }
    truncated = score_retention(
        "rolling_truncation", rolling_truncation(events, max_events=3), required
    )
    compacted = score_retention(
        "state_preserving_compaction", state_preserving_compaction(events), required
    )
    return {
        "schema_version": "1.0",
        "suite": "synthetic_harness_fidelity",
        "scope": "deterministic state-retention fixture; no model/provider invoked",
        "status": "PASS" if compacted.passed else "FAIL",
        "comparison": [asdict(truncated), asdict(compacted)],
        "interpretation": {
            "rolling_truncation_passed": truncated.passed,
            "state_preserving_compaction_passed": compacted.passed,
            "real_model_effect": "NOT RUN",
        },
        "limitations": [
            "This is not a benchmark of a provider's actual context or compaction implementation.",
            "Synthetic fact retention does not establish improved task success.",
            "A real summary must be validated against source events and task requirements.",
        ],
    }


if __name__ == "__main__":
    import json

    print(json.dumps(build_fixture(), indent=2))
