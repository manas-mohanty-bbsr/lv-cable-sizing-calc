import json
from pathlib import Path

import pytest

from cablecalc.codes import load_code
from cablecalc.core import size_cable
from cablecalc.models import CableInput

CASES = sorted((Path(__file__).parent / "worked_examples").glob("*.json"))


def test_there_are_at_least_two_cases_per_code():
    codes = [json.loads(p.read_text(encoding="utf-8"))["code"] for p in CASES]
    for code in ("IEC", "IS"):
        assert codes.count(code) >= 2, f"need 2 hand-checked {code} cases"


@pytest.mark.parametrize("path", CASES, ids=lambda p: p.stem)
def test_worked_example(path):
    case = json.loads(path.read_text(encoding="utf-8"))
    assert case["checked_by"], f"{path.name} has not been signed off"
    r = size_cable(CableInput(**case["input"]), load_code(case["code"]))
    exp, tol = case["expected"], case["tolerance_pct"] / 100
    assert r.size_mm2 == exp["size_mm2"]
    assert r.governing == exp["governing"]
    got = {c.name: c for c in r.checks}
    assert got["current"].actual == pytest.approx(exp["iz_a"], rel=tol)
    assert got["voltage_drop"].actual == pytest.approx(exp["vd_pct"], rel=tol)
    assert got["short_circuit"].required == pytest.approx(exp["smin_mm2"], rel=tol)
