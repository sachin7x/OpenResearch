"""Regression tests for synthetic harness-fidelity fixtures."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.harness_fidelity import (  # noqa: E402
    Event,
    build_fixture,
    rolling_truncation,
    score_retention,
    state_preserving_compaction,
)


class HarnessFidelityTests(unittest.TestCase):
    def test_rolling_truncation_can_drop_early_constraints(self):
        fixture = build_fixture()
        rolling, _ = fixture["comparison"]
        self.assertFalse(rolling["passed"])
        self.assertIn("must_not_use_network", rolling["missing_facts"])

    def test_state_preserving_compaction_retains_required_facts(self):
        fixture = build_fixture()
        _, compacted = fixture["comparison"]
        self.assertTrue(compacted["passed"])
        self.assertEqual(compacted["missing_facts"], [])

    def test_compaction_keeps_latest_value_for_duplicate_fact_key(self):
        events = [
            Event(1, "observation", "auth", "unknown"),
            Event(2, "observation", "auth", "denied"),
        ]
        retained = state_preserving_compaction(events)
        result = score_retention("test", retained, {"auth": "denied"})
        self.assertTrue(result.passed)
        self.assertEqual(len(retained), 1)
        self.assertEqual(retained[0].sequence, 2)

    def test_zero_event_window_retains_nothing(self):
        events = [Event(1, "constraint", "network", "forbidden")]
        self.assertEqual(rolling_truncation(events, 0), [])

    def test_negative_event_window_is_rejected(self):
        with self.assertRaises(ValueError):
            rolling_truncation([], -1)

    def test_results_do_not_claim_real_model_effect(self):
        fixture = build_fixture()
        self.assertEqual(fixture["interpretation"]["real_model_effect"], "NOT RUN")
        self.assertIn("no model/provider invoked", fixture["scope"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
