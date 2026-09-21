"""Data shapes shared by every layer. No calculation lives here."""
from __future__ import annotations

import math
from dataclasses import dataclass


class InputError(ValueError):
    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("; ".join(problems))


@dataclass(frozen=True)
class CableInput:
    tag: str
    phase: str
    voltage_v: float
    design_current_a: float
    power_factor: float
    length_m: float
    conductor: str
    insulation: str
    method: str
    cores: int
    ambient_c: float
    grouped_circuits: int
    vd_limit_pct: float
    fault_current_ka: float
    fault_time_s: float
    device_rating_a: float | None = None


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    required: float
    actual: float
    unit: str
    higher_is_better: bool
    formula: str
    sources: tuple[str, ...]
    detail: str

    @property
    def margin(self) -> float:
        if self.higher_is_better:
            return self.actual / self.required
        return self.required / self.actual


@dataclass(frozen=True)
class SizingResult:
    tag: str
    code: str
    size_mm2: float | None
    checks: tuple[CheckResult, ...]
    governing: str | None
    passed: bool
    message: str


_POSITIVE = ("voltage_v", "design_current_a", "length_m", "vd_limit_pct",
             "fault_current_ka", "fault_time_s")


def validate_input(inp: CableInput) -> None:
    p: list[str] = []

    def bad(field: str, reason: str) -> None:
        p.append(f"{inp.tag}: field '{field}' {reason}")

    if inp.phase not in ("1ph", "3ph"):
        bad("phase", "must be '1ph' or '3ph'")
    if inp.conductor not in ("Cu", "Al"):
        bad("conductor", "must be 'Cu' or 'Al'")
    if inp.insulation not in ("PVC", "XLPE"):
        bad("insulation", "must be 'PVC' or 'XLPE'")
    for f in _POSITIVE:
        if not getattr(inp, f) > 0:
            bad(f, "must be greater than 0")
    if not 0 < inp.power_factor <= 1:
        bad("power_factor", "must be between 0 and 1")
    if inp.grouped_circuits < 1:
        bad("grouped_circuits", "must be 1 or more")
    if inp.cores < 1:
        bad("cores", "must be 1 or more")
    if inp.device_rating_a is not None and inp.device_rating_a <= 0:
        bad("device_rating_a", "must be greater than 0")
    if p:
        raise InputError(p)


def design_current_from_kw(kw: float, voltage_v: float, power_factor: float, phase: str) -> float:
    watts = kw * 1000
    if phase == "3ph":
        return watts / (math.sqrt(3) * voltage_v * power_factor)
    return watts / (voltage_v * power_factor)
