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
    cable: str
    ambient_c: float
    grouped_circuits: int
    vd_limit_pct: float
    fault_current_ka: float
    fault_time_s: float
    device_rating_a: float | None = None
    soil_resistivity_kmw: float = 2.5
    row: int | None = None

    @property
    def loaded_conductors(self) -> int:
        """Current-carrying conductors: line and neutral on 1ph, the three lines on 3ph."""
        return 2 if self.phase == "1ph" else 3


# Cable constructions offered, and the phase each may be used on.
CABLES = {"2 x 1C": ("1ph",), "3 x 1C": ("3ph",), "4 x 1C": ("3ph",), "2C": ("1ph",),
          "3C": ("1ph", "3ph"), "3.5C": ("3ph",), "4C": ("3ph",)}


def is_single_core(cable: str) -> bool:
    return cable.endswith("x 1C")


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
    cable: str = ""
    material: str = ""

    @property
    def heading(self) -> str:
        """E.g. 'Cable F-04: 3.5C x 185 mm2 Al PVC'."""
        if self.size_mm2 is None:
            return f"Cable {self.tag}: {self.cable} {self.material}, no size passes"
        return f"Cable {self.tag}: {self.cable} x {self.size_mm2:g} mm2 {self.material}"


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
    if inp.cable not in CABLES:
        bad("cable", "must be one of " + ", ".join(CABLES))
    elif inp.phase in ("1ph", "3ph") and inp.phase not in CABLES[inp.cable]:
        bad("cable", f"'{inp.cable}' needs phase {CABLES[inp.cable][0]}")
    elif is_single_core(inp.cable) and inp.method == "E":
        bad("cable", "single-core cables in free air are methods F and G (IS 732 Table 19 items "
            "31 to 33), which this tool does not cover")
    elif is_single_core(inp.cable) and inp.method == "A2":
        bad("cable", "method A2 is for multi-core cable; for single-core cables in conduit in an "
            "insulated wall use A1 (IS 732 Table 19 item 1)")
    if not inp.soil_resistivity_kmw > 0:
        bad("soil_resistivity_kmw", "must be greater than 0")
    if inp.device_rating_a is not None and inp.device_rating_a <= 0:
        bad("device_rating_a", "must be greater than 0")
    if p:
        raise InputError(p)


def design_current_from_kw(kw: float, voltage_v: float, power_factor: float, phase: str) -> float:
    watts = kw * 1000
    if phase == "3ph":
        return watts / (math.sqrt(3) * voltage_v * power_factor)
    return watts / (voltage_v * power_factor)
