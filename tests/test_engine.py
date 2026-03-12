"""Tests for the research engine — confidence scoring and data structures."""

import tempfile

from src.why.brain import Brain
from src.why.engine import (
    Finding,
    DepthResult,
    research_confidence,
    usefulness_to_bangs,
)


def _fresh_brain():
    return Brain(path=tempfile.mkdtemp())


class TestUsefulnessToBangs:
    def test_high_combined(self):
        assert usefulness_to_bangs(1.0, 1.0) == "!!!!"

    def test_medium_combined(self):
        assert usefulness_to_bangs(0.7, 0.5) in ("!!", "!!!")

    def test_low_combined(self):
        assert usefulness_to_bangs(0.2, 0.0) == ""


class TestResearchConfidence:
    def _make_findings(self, n, usefulness=0.8, surprise=0.2):
        return [
            Finding(
                title=f"finding {i}",
                content="content",
                url=f"https://source{i}.com",
                usefulness=usefulness,
                predicted=0.5,
                surprise=surprise,
                bangs="!",
                depth=0,
            )
            for i in range(n)
        ]

    def test_no_findings_zero_confidence(self):
        brain = _fresh_brain()
        result = research_confidence([], brain)
        assert result["confidence"] == 0.0

    def test_good_results_high_confidence(self):
        brain = _fresh_brain()
        # Build some calibration
        for _ in range(10):
            brain.record(0.5, 0.7, "calibration query")

        findings = self._make_findings(10, usefulness=0.85, surprise=0.2)
        dr = DepthResult(
            depth=0, findings=findings, n_searched=5, n_useful=10, n_surprise=0
        )
        result = research_confidence([dr], brain)
        assert result["confidence"] > 0.5

    def test_mixed_results_lower_confidence(self):
        brain = _fresh_brain()
        # Mix of very useful and useless
        findings = []
        for i in range(10):
            findings.append(
                Finding(
                    title=f"f{i}",
                    content="c",
                    url=f"https://s{i}.com",
                    usefulness=1.0 if i % 2 == 0 else 0.0,
                    predicted=0.5,
                    surprise=0.1,
                    bangs="",
                    depth=0,
                )
            )
        dr = DepthResult(
            depth=0, findings=findings, n_searched=5, n_useful=5, n_surprise=0
        )
        result = research_confidence([dr], brain)
        # High variance = lower consistency = lower confidence
        assert result["breakdown"]["consistency"] < 0.5

    def test_deeper_research_higher_depth_score(self):
        brain = _fresh_brain()
        f1 = self._make_findings(3)
        f2 = self._make_findings(3)
        f3 = self._make_findings(3)
        dr0 = DepthResult(depth=0, findings=f1, n_searched=3, n_useful=3)
        dr1 = DepthResult(depth=1, findings=f2, n_searched=3, n_useful=3)
        dr2 = DepthResult(depth=2, findings=f3, n_searched=3, n_useful=3)

        shallow = research_confidence([dr0], brain)
        deep = research_confidence([dr0, dr1, dr2], brain)
        assert deep["breakdown"]["depth_coverage"] > shallow["breakdown"]["depth_coverage"]

    def test_confidence_breakdown_keys(self):
        brain = _fresh_brain()
        findings = self._make_findings(5)
        dr = DepthResult(depth=0, findings=findings, n_searched=3, n_useful=5)
        result = research_confidence([dr], brain)
        assert "confidence" in result
        assert "breakdown" in result
        assert "consistency" in result["breakdown"]
        assert "calibration" in result["breakdown"]
        assert "source_diversity" in result["breakdown"]
        assert "surprise_balance" in result["breakdown"]
        assert "depth_coverage" in result["breakdown"]

    def test_confidence_in_range(self):
        brain = _fresh_brain()
        findings = self._make_findings(5)
        dr = DepthResult(depth=0, findings=findings, n_searched=3, n_useful=5)
        result = research_confidence([dr], brain)
        assert 0.0 <= result["confidence"] <= 1.0
