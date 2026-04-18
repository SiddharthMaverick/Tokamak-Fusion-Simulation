"""
tests/test_physics.py
=====================
Unit tests for src/physics.py.
Run with:  pytest tests/
"""

import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.physics import (
    derivedParams,
    is_disruption_risk,
    is_troyon_unstable,
    stability_summary,
    DerivedParams,
)


# ── Helpers ───────────────────────────────────────────────────────────
def approx(a: float, b: float, tol: float = 1e-6) -> bool:
    return abs(a - b) < tol


# ── derivedParams ─────────────────────────────────────────────────────

class TestDerivedParams:

    def test_returns_dataclass(self):
        d = derivedParams(2.0, 3.5, 20, 4.0)
        assert isinstance(d, DerivedParams)

    def test_q_calibration_point(self):
        """At Ip=2 MA, Bt=3.5 T the calibration target is q=2.5."""
        d = derivedParams(2.0, 3.5, 20, 4.0)
        assert approx(d.q, 2.5, tol=1e-4), f"Expected q≈2.5, got {d.q}"

    def test_q_increases_with_bt(self):
        """Higher toroidal field → higher safety factor."""
        d1 = derivedParams(2.0, 3.5, 20, 4.0)
        d2 = derivedParams(2.0, 5.0, 20, 4.0)
        assert d2.q > d1.q

    def test_q_decreases_with_ip(self):
        """Higher plasma current → lower safety factor."""
        d1 = derivedParams(2.0, 3.5, 20, 4.0)
        d2 = derivedParams(4.0, 3.5, 20, 4.0)
        assert d2.q < d1.q

    def test_q_lower_bound(self):
        """q must always be ≥ 0.5 even at extreme inputs."""
        d = derivedParams(5.0, 1.0, 100, 12.0)
        assert d.q >= 0.5

    def test_beta_increases_with_pnbi(self):
        """More NBI heating → higher β_N."""
        d1 = derivedParams(2.0, 3.5, 10, 4.0)
        d2 = derivedParams(2.0, 3.5, 80, 4.0)
        assert d2.beta_N > d1.beta_N

    def test_beta_decreases_with_bt(self):
        """Stronger toroidal field → lower β_N (harder to drive)."""
        d1 = derivedParams(2.0, 3.5, 40, 4.0)
        d2 = derivedParams(2.0, 6.0, 40, 4.0)
        assert d2.beta_N < d1.beta_N

    def test_beta_decreases_with_ne(self):
        """Higher density → lower β_N proxy (more collisional damping)."""
        d1 = derivedParams(2.0, 3.5, 40, 2.0)
        d2 = derivedParams(2.0, 3.5, 40, 10.0)
        assert d2.beta_N < d1.beta_N

    def test_vtor_zero_at_no_nbi(self):
        """No NBI → v_tor ≈ 0."""
        d = derivedParams(2.0, 3.5, 0, 4.0)
        assert approx(d.v_tor, 0.0, tol=1e-6)

    def test_vtor_increases_with_pnbi(self):
        """More NBI → faster rotation."""
        d1 = derivedParams(2.0, 3.5, 10, 4.0)
        d2 = derivedParams(2.0, 3.5, 80, 4.0)
        assert d2.v_tor > d1.v_tor

    def test_turb_capped_at_090(self):
        """Turbulence must never exceed 0.90."""
        # Extreme: high β, low q
        d = derivedParams(5.0, 1.0, 100, 1.0)
        assert d.turb <= 0.90

    def test_turb_non_negative(self):
        """Turbulence must be ≥ 0."""
        d = derivedParams(0.5, 8.0, 0, 12.0)
        assert d.turb >= 0.0

    def test_vel_clamped(self):
        """Angular step must stay within [0.003, 0.18] rad/frame."""
        for pnbi in [0, 5, 50, 100]:
            for ne_ in [1.0, 4.0, 12.0]:
                d = derivedParams(2.0, 3.5, pnbi, ne_)
                assert 0.003 <= d.vel <= 0.18, \
                    f"vel={d.vel} out of bounds at pnbi={pnbi}, ne={ne_}"

    def test_zero_pnbi_zero_turb(self):
        """No NBI heating → no turbulence (β_N ≈ 0 → turb ≈ 0)."""
        d = derivedParams(2.0, 3.5, 0, 4.0)
        assert approx(d.turb, 0.0, tol=1e-6)


# ── Stability checks ──────────────────────────────────────────────────

class TestStabilityChecks:

    def test_disruption_risk_when_q_low(self):
        """Kruskal-Shafranov: q < 2 → disruption risk."""
        # Ip high, Bt low → q < 2
        d = derivedParams(4.0, 2.0, 20, 4.0)
        if d.q < 2.0:
            assert is_disruption_risk(d)

    def test_no_disruption_risk_when_q_high(self):
        """q well above 2 → no disruption risk."""
        d = derivedParams(1.0, 8.0, 20, 4.0)
        assert not is_disruption_risk(d)

    def test_troyon_unstable_flag(self):
        """β_N > 3.5 → Troyon unstable."""
        # Need very high P_NBI, low ne, low Bt
        d = derivedParams(2.0, 1.5, 100, 1.0)
        if d.beta_N > 3.5:
            assert is_troyon_unstable(d)

    def test_troyon_stable_flag(self):
        """Normal operating point → Troyon stable."""
        d = derivedParams(2.0, 3.5, 20, 4.0)
        assert not is_troyon_unstable(d)

    def test_stability_summary_nominal(self):
        """Nominal operating point → summary says stable."""
        d = derivedParams(2.0, 3.5, 20, 4.0)
        summary = stability_summary(d)
        assert "Stable" in summary

    def test_stability_summary_disruption(self):
        """q < 2 → disruption keyword in summary."""
        d = derivedParams(5.0, 1.5, 10, 4.0)
        if d.q < 2.0:
            summary = stability_summary(d)
            assert "disruption" in summary.lower() or "tearing" in summary.lower()


# ── Edge cases ────────────────────────────────────────────────────────

class TestEdgeCases:

    def test_minimum_inputs(self):
        """Slider minimum values must not crash or produce NaN."""
        d = derivedParams(0.5, 1.0, 0, 1.0)
        assert math.isfinite(d.q)
        assert math.isfinite(d.beta_N)
        assert math.isfinite(d.v_tor)
        assert math.isfinite(d.turb)
        assert math.isfinite(d.vel)

    def test_maximum_inputs(self):
        """Slider maximum values must not crash or produce NaN."""
        d = derivedParams(5.0, 8.0, 100, 12.0)
        assert math.isfinite(d.q)
        assert math.isfinite(d.beta_N)
        assert math.isfinite(d.v_tor)
        assert math.isfinite(d.turb)
        assert math.isfinite(d.vel)

    def test_bt_dominates_q_over_ip(self):
        """
        For fixed Ip, doubling Bt should approximately double q.
        This verifies the linear scaling in the KS approximation.
        """
        d1 = derivedParams(2.0, 2.0, 20, 4.0)
        d2 = derivedParams(2.0, 4.0, 20, 4.0)
        ratio = d2.q / d1.q
        assert approx(ratio, 2.0, tol=1e-3), \
            f"Expected q ratio ≈ 2.0, got {ratio:.4f}"
