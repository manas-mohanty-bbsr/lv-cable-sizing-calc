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


def test_governing_is_the_check_that_fails_one_size_down():
    # Manas's case 1 (IEC): at 25 mm2 current has the smallest margin (1.32 vs SC 1.52),
    # but 16 mm2 fails only on short circuit (16 < 16.50), so short circuit governs.
    from cablecalc.codes import load_code
    inp = make(tag="WE1", voltage_v=415, design_current_a=42, power_factor=0.85, length_m=65,
               ambient_c=40, grouped_circuits=3, fault_current_ka=6, device_rating_a=50)
    r = size_cable(inp, load_code("IEC"))
    assert r.size_mm2 == 25 and r.governing == "short_circuit"


def test_when_two_checks_fail_one_size_down_the_worse_one_governs(fixture_data):
    # 4 mm2 fails current (margin 28.71/30 = 0.957) and SC (4/5.4996 = 0.727): SC is worse.
    assert size_cable(make(), fixture_data).governing == "short_circuit"


def test_smallest_tabulated_size_has_no_governing_check(fixture_data):
    r = size_cable(make(design_current_a=10, ambient_c=30, length_m=10, fault_current_ka=0.5),
                   fixture_data)
    assert r.size_mm2 == 2.5 and r.governing is None
    assert "smallest size in the table" in r.message
