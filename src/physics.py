"""
src/physics.py
==============
Pure-Python physics kernel for the Tokamak MHD simulation.

All formulae are dimensionally motivated simplifications of the
real tokamak physics, calibrated to give physically reasonable
numbers at ITER-like operating points.

References
----------
- Wesson, J. (2004). Tokamaks (3rd ed.). Oxford University Press.
- Freidberg, J. P. (2007). Plasma Physics and Fusion Energy. Cambridge UP.
- ITER Physics Basis, Nucl. Fusion 39 (1999) 2175.
"""

from __future__ import annotations
from dataclasses import dataclass
import math


# ── Operating-point calibration constants ─────────────────────────────
# At Ip=2 MA, Bt=3.5 T  →  q ≈ 2.5  (ITER baseline ≈ 3.0 at 15 MA/5.3 T)
_K_Q: float = (2.5 * 2.0) / 3.5   # ≈ 1.4286


@dataclass
class DerivedParams:
    """Physics state derived from the four operator control inputs."""

    # Safety factor (cylindrical Kruskal-Shafranov approximation)
    q: float
    # Normalised beta (Troyon proxy)
    beta_N: float
    # Toroidal rotation velocity proxy [km/s display units]
    v_tor: float
    # Ballooning turbulence amplitude δB/B  (dimensionless, 0–1)
    turb: float
    # Angular advance per render frame [rad] (proportional to v_tor)
    vel: float


def derivedParams(
    ip: float,    # Plasma current  [MA]
    bt: float,    # Toroidal field  [T]
    pnbi: float,  # NBI heating power [MW]
    ne: float,    # Electron density  [10^19 m^-3]
) -> DerivedParams:
    """
    Compute all derived plasma parameters from the four control inputs.

    Parameters
    ----------
    ip   : Plasma current in MA (0.5 – 5.0)
    bt   : Toroidal field in T  (1.0 – 8.0)
    pnbi : NBI heating power in MW (0 – 100)
    ne   : Electron density in 10^19 m^-3 (1.0 – 12.0)

    Returns
    -------
    DerivedParams dataclass with q, beta_N, v_tor, turb, vel.

    Physics notes
    -------------
    q (safety factor)
        Cylindrical KS approximation: q ≈ a²·Bt / (R·μ₀·Ip/2π)
        Simplified to q = k_q · Bt / Ip with k_q calibrated at
        Ip=2 MA, Bt=3.5 T → q=2.5.
        Disruption risk when q < 2 (Kruskal-Shafranov criterion).

    β_N (normalised pressure)
        Troyon proxy: β_N ∝ P_heat / (ne · Bt²).
        Troyon stability limit: β_N < 3.5 (%·m·T/MA).

    v_tor (toroidal rotation)
        NBI deposits momentum ∝ P_NBI; collisional damping ∝ ne.
        Display units are arbitrary km/s proxy.

    δB/B (turbulence)
        Ideal ballooning drive ∝ β_N / q².
        Capped at 0.90 to keep the simulation visually bounded.

    vel (render angular step)
        Proportional to v_tor, clamped to [0.003, 0.18] rad/frame
        so the simulation stays visually smooth at all slider positions.
    """
    # Safety factor — ensure physical lower bound
    q_val = max(0.5, _K_Q * bt / max(ip, 1e-6))

    # Normalised beta
    beta_N = (pnbi * 2.8) / (ne * bt * bt + 0.1)

    # Toroidal velocity proxy [km/s]
    v_tor = (pnbi * 18.0) / (ne * 1.2 + 0.5)

    # Ballooning turbulence drive (capped before disruption diverges)
    turb = min(0.90, max(0.0, beta_N / (q_val * q_val * 3.2 + 0.1)))

    # Angular advance per render frame
    vel = min(0.18, max(0.003, v_tor * 0.0032))

    return DerivedParams(
        q=q_val,
        beta_N=beta_N,
        v_tor=v_tor,
        turb=turb,
        vel=vel,
    )


def is_disruption_risk(params: DerivedParams) -> bool:
    """Return True if q < 2 (Kruskal-Shafranov disruption criterion)."""
    return params.q < 2.0


def is_troyon_unstable(params: DerivedParams) -> bool:
    """Return True if β_N > 3.5 (Troyon stability limit)."""
    return params.beta_N > 3.5


def stability_summary(params: DerivedParams) -> str:
    """Human-readable one-line stability assessment."""
    issues = []
    if is_disruption_risk(params):
        issues.append(f"q={params.q:.2f} < 2 — tearing/disruption risk")
    if is_troyon_unstable(params):
        issues.append(f"β_N={params.beta_N:.2f} > 3.5 — Troyon limit exceeded")
    return " | ".join(issues) if issues else "Stable operating point"
