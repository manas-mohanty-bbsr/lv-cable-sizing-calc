"""The calculation core. Deterministic; every value it uses comes from a sourced table."""
from __future__ import annotations

import math

from .data import CodeData
from .models import CableInput, CheckResult, SizingResult, validate_input


BURIED_METHODS = ("D1", "D2")


def check_current(inp: CableInput, size_mm2: float, data: CodeData) -> CheckResult:
    it, s1 = data.ampacity(inp.conductor, inp.insulation, inp.method, inp.cores, size_mm2)
    required = max(inp.design_current_a, inp.device_rating_a or 0)
    if inp.method not in BURIED_METHODS:
        ca, s2 = data.temp_factor(inp.insulation, inp.ambient_c)
        cg, s3 = data.group_factor(inp.method, inp.grouped_circuits)
        iz = it * ca * cg
        return CheckResult(
            name="current", passed=iz >= required, required=required, actual=iz, unit="A",
            higher_is_better=True, formula="Iz = It x Ca x Cg >= max(Ib, In)",
            sources=(s1, s2, s3),
            detail=f"It = {it:g} A, Ca = {ca:g}, Cg = {cg:g}, Iz = {iz:.2f} A")
    # Buried: ambient is the ground temperature, soil resistivity applies, and grouping
    # assumes the cables or ducts are touching (the worst case).
    ca, s2 = data.temp_factor(inp.insulation, inp.ambient_c, medium="ground")
    cs, s3 = data.soil_factor(inp.method, inp.soil_resistivity_kmw)
    cg, s4 = data.group_factor(inp.method, inp.grouped_circuits)
    s4 = f"{s4} (cables or ducts touching assumed)"
    iz = it * ca * cs * cg
    return CheckResult(
        name="current", passed=iz >= required, required=required, actual=iz, unit="A",
        higher_is_better=True, formula="Iz = It x Ca x Cs x Cg >= max(Ib, In)",
        sources=(s1, s2, s3, s4),
        detail=f"It = {it:g} A, Ca = {ca:g} (ground), Cs = {cs:g}, Cg = {cg:g}, Iz = {iz:.2f} A")


def check_voltage_drop(inp: CableInput, size_mm2: float, data: CodeData) -> CheckResult:
    r, x, src = data.impedance(inp.conductor, inp.insulation, size_mm2)
    pf = inp.power_factor
    sin_phi = math.sqrt(max(0.0, 1 - pf * pf))
    b = math.sqrt(3) if inp.phase == "3ph" else 2.0
    du = b * inp.design_current_a * (inp.length_m / 1000) * (r * pf + x * sin_phi)
    pct = 100 * du / inp.voltage_v
    return CheckResult(
        name="voltage_drop", passed=pct <= inp.vd_limit_pct, required=inp.vd_limit_pct,
        actual=pct, unit="%", higher_is_better=False,
        formula="dU = b x Ib x L x (R cos phi + X sin phi); b = sqrt(3) (3-phase, on line voltage) or 2 (single-phase)",
        sources=(src,),
        detail=f"R = {r:g} ohm/km, X = {x:g} ohm/km, L = {inp.length_m:g} m, dU = {du:.2f} V")


def check_short_circuit(inp: CableInput, size_mm2: float, data: CodeData) -> CheckResult:
    k, src = data.k_factor(inp.conductor, inp.insulation)
    smin = inp.fault_current_ka * 1000 * math.sqrt(inp.fault_time_s) / k
    return CheckResult(
        name="short_circuit", passed=size_mm2 >= smin, required=smin, actual=float(size_mm2),
        unit="mm2", higher_is_better=True, formula="S >= I x sqrt(t) / k",
        sources=(src,),
        detail=f"I = {inp.fault_current_ka:g} kA, t = {inp.fault_time_s:g} s, k = {k:g}")


def governing_check(checks: tuple[CheckResult, ...]) -> str:
    return min(checks, key=lambda c: c.margin).name


def size_cable(inp: CableInput, data: CodeData) -> SizingResult:
    validate_input(inp)
    sizes = data.sizes(inp.conductor, inp.insulation, inp.method, inp.cores)
    checks: tuple[CheckResult, ...] = ()
    for size in sizes:
        checks = (check_current(inp, size, data),
                  check_voltage_drop(inp, size, data),
                  check_short_circuit(inp, size, data))
        if all(c.passed for c in checks):
            return SizingResult(inp.tag, data.code, size, checks, governing_check(checks),
                                True, f"{size:g} mm2 passes all checks")
    return SizingResult(inp.tag, data.code, None, checks, None, False,
                        f"No size passes. Results shown are for the largest size in the table "
                        f"({sizes[-1]:g} mm2).")
