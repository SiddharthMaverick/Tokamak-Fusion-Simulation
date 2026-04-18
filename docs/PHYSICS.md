# Physics Documentation

## Tokamak geometry

The simulation uses ITER-scale parameters:

| Parameter | Symbol | Value |
|---|---|---|
| Major radius | R₀ | 10 units (≈ 6.2 m for ITER) |
| Minor radius | a | 3 units (≈ 2.0 m for ITER) |
| Aspect ratio | R₀/a | 3.33 |

### Coordinate system

Follows the Three.js r128 `TorusGeometry` convention exactly:

```
x = (R₀ + ρ·cos φ)·cos θ
y = (R₀ + ρ·cos φ)·sin θ    ← XY plane is equatorial (big ring)
z =  ρ·sin φ                 ← Z is the poloidal axis
```

where `θ` is the toroidal angle and `φ` is the poloidal angle.

## Safety factor q

The safety factor measures how many toroidal turns a field line makes per poloidal turn:

```
q = dΦ_tor / dΦ_pol
```

In the cylindrical (large-aspect-ratio) approximation:

```
q ≈ r·Bt / (R·Bpol) ≈ a²·Bt / (R₀·μ₀·Ip / 2π)
```

Simplified to `q = k_q · Bt / Ip` with `k_q ≈ 1.4286` calibrated at the ITER baseline.

### Stability criterion

- **q < 2**: Kruskal-Shafranov criterion violated → tearing mode / disruption risk
- **q = 1**: Internal kink mode (sawtooth oscillations in real machines)
- **q > 3**: Comfortably stable edge

## Normalised beta β_N

Measures plasma pressure relative to magnetic pressure, normalised to machine size:

```
β = 2μ₀⟨p⟩ / Bt²
β_N = β · (a·Bt / Ip)    [units: %·m·T/MA]
```

In the simulation: `β_N ∝ P_NBI / (ne · Bt²)`

**Troyon limit**: `β_N < 3.5` — above this, ideal MHD ballooning modes go unstable.

## Toroidal rotation

NBI injects fast neutrals that ionise inside the plasma and deposit toroidal momentum:

```
v_tor ∝ P_NBI / (ne · R₀)
```

Higher density increases collisional damping, reducing rotation for fixed power.

## Ballooning turbulence

The simulation models the turbulence amplitude as:

```
δB/B ∝ β_N / q²
```

This is the ideal ballooning drive — pressure-gradient-driven interchange modes stabilised by magnetic shear (∝ q). The factor 1/q² comes from the stabilising effect of field-line bending.

Radial perturbations are applied via multi-octave smooth noise scaled by δB/B:

```
ρ(t+dt) = ρ(t) + noise3(θ, φ·q, t) · (δB/B) · a
```

The field-aligned coordinate `φ·q` ensures the noise is correlated along field lines, mimicking real ballooning-mode structure.

## Particle dynamics

Each tracer follows the (ι, 1) winding of the magnetic field:

```
Δθ = vel · speed_i         (toroidal step, proportional to v_tor)
Δφ = Δθ / q               (poloidal step, rotational transform ι = 1/q)
```

This produces the helical orbits characteristic of confined plasma in a tokamak. At q = 2, particles complete exactly 2 toroidal turns per poloidal turn (2/1 rational surface). At q = 3/2, they close after 3 toroidal / 2 poloidal turns.
