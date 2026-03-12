"""Tests for the persistent learning brain (public core)."""

import json
import tempfile
from pathlib import Path

from src.why.brain import Brain


def _fresh_brain(tmp_path=None):
    """Create a brain with a temp directory so tests don't pollute ~/.why."""
    if tmp_path is None:
        tmp_path = tempfile.mkdtemp()
    return Brain(path=tmp_path)


class TestBrainBasics:
    def test_fresh_brain_has_zero_state(self):
        brain = _fresh_brain()
        assert brain.data["sessions"] == 0
        assert brain.data["total_searches"] == 0
        assert brain.level == 0
        assert brain.calibration == 0.0

    def test_start_session_increments(self):
        brain = _fresh_brain()
        brain.start_session()
        assert brain.data["sessions"] == 1
        brain.start_session()
        assert brain.data["sessions"] == 2

    def test_record_updates_counts(self):
        brain = _fresh_brain()
        brain.record(0.5, 0.8, "test query")
        assert brain.data["total_searches"] == 1
        assert brain.data["total_useful"] == 1  # 0.8 >= 0.6

    def test_record_low_usefulness_not_counted(self):
        brain = _fresh_brain()
        brain.record(0.5, 0.3, "test query")
        assert brain.data["total_searches"] == 1
        assert brain.data["total_useful"] == 0

    def test_surprise_normalized_0_to_1(self):
        brain = _fresh_brain()
        for i in range(20):
            surprise = brain.record(0.5, 0.5 + (i % 3) * 0.1, f"query {i}")
            assert 0.0 <= surprise <= 1.0

    def test_learn_adds_pattern(self):
        brain = _fresh_brain()
        brain.learn("test pattern")
        assert "test pattern" in brain.data["learnings"]
        assert brain.level == 1

    def test_learn_deduplicates(self):
        brain = _fresh_brain()
        brain.learn("same pattern")
        brain.learn("same pattern")
        assert brain.data["learnings"].count("same pattern") == 1


class TestBrainPriors:
    def test_prior_defaults_to_0_5(self):
        brain = _fresh_brain()
        assert brain.get_prior("unknown topic") == 0.5

    def test_prior_updates_after_records(self):
        brain = _fresh_brain()
        for _ in range(5):
            brain.record(0.5, 0.9, "quantum computing basics")
        prior = brain.get_prior("quantum computing basics")
        assert prior > 0.5

    def test_prior_needs_min_observations(self):
        brain = _fresh_brain()
        brain.record(0.5, 0.9, "rare topic xyz")
        assert brain.get_prior("rare topic xyz") == 0.5


class TestBrainStrategies:
    def test_strategy_extraction(self):
        brain = _fresh_brain()
        brain.record(0.5, 0.8, "how does mechanism work")
        assert "mechanism" in brain.data["strategies"]

    def test_combo_strategy(self):
        brain = _fresh_brain()
        brain.record(0.5, 0.8, "latest mechanism comparison vs other")
        strategies = brain.data["strategies"]
        combo_found = any(k.startswith("combo:") for k in strategies)
        assert combo_found

    def test_best_strategies_returns_top(self):
        brain = _fresh_brain()
        for _ in range(5):
            brain.record(0.5, 0.9, "how mechanism works")
            brain.record(0.5, 0.3, "latest news 2026")
        best = brain.best_strategies(1)
        assert len(best) >= 1


class TestBrainQueryValue:
    def test_query_value_returns_float(self):
        brain = _fresh_brain()
        val = brain.query_value("how does X work", 0.7)
        assert isinstance(val, float)

    def test_unknown_topic_has_high_epistemic_value(self):
        brain = _fresh_brain()
        val_unknown = brain.query_value("completely novel topic xyz", 0.5)
        for _ in range(20):
            brain.record(0.5, 0.5, "well known topic")
        val_known = brain.query_value("well known topic", 0.5)
        assert val_unknown < val_known


class TestBrainPersistence:
    def test_save_and_reload(self):
        tmp = tempfile.mkdtemp()
        brain = Brain(path=tmp)
        brain.record(0.5, 0.8, "test persistence")
        brain.learn("persistence works")

        brain2 = Brain(path=tmp)
        assert brain2.data["total_searches"] == 1
        assert "persistence works" in brain2.data["learnings"]


class TestBrainSummary:
    def test_summary_string(self):
        brain = _fresh_brain()
        s = brain.summary()
        assert "Sessions:" in s
        assert "Searches:" in s

    def test_calibration_property(self):
        brain = _fresh_brain()
        assert brain.calibration == 0.0
        brain.record(0.5, 0.5, "test")
        assert brain.calibration > 0.0
