import pytest
from cablecalc.core import size_cable
from cablecalc.models import InputError
from tests.test_models import make


def test_smallest_passing_size_and_governing_check(fixture_data):
    r = size_cable(make(), fixture_data)
    # 4 mm2 fails on current; 6 mm2 passes all.
    # Margins at 6: current 37.41/30 = 1.247, VD 5/1.7498 = 2.857, SC 6/5.4996 = 1.091
    assert r.passed and r.size_mm2 == 6 and r.governing == "short_circuit"
    assert [c.name for c in r.checks] == ["current", "voltage_drop", "short_circuit"]


def test_long_run_governed_by_voltage_drop(fixture_data):
    r = size_cable(make(length_m=350), fixture_data)
    # 10 mm2: VD = 7.52 % FAIL; 16 mm2: dU = sqrt(3) x 30 x 0.35 x 1.048 = 19.06 V = 4.765 %
    assert r.size_mm2 == 16 and r.governing == "voltage_drop"


def test_no_size_passes(fixture_data):
    r = size_cable(make(length_m=400), fixture_data)
    # 16 mm2 at 400 m: 5.446 % > 5 %
    assert not r.passed and r.size_mm2 is None
    assert "largest size in the table (16 mm2)" in r.message
    assert any(not c.passed for c in r.checks)


def test_single_phase_governed_by_short_circuit(fixture_data):
    inp = make(phase="1ph", voltage_v=230, design_current_a=20, power_factor=1.0,
               length_m=30, ambient_c=30, fault_current_ka=1)
    # 2.5 fails SC (Smin 2.75); 4 passes all; margins: I 1.65, VD 1.917, SC 1.455
    r = size_cable(inp, fixture_data)
    assert r.size_mm2 == 4 and r.governing == "short_circuit"


def test_invalid_input_raises_before_calculating(fixture_data):
    with pytest.raises(InputError):
        size_cable(make(length_m=0), fixture_data)
