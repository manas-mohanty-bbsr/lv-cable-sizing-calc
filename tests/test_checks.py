import pytest
from cablecalc.core import check_current, check_short_circuit, check_voltage_drop
from tests.test_models import make


def test_current_fails_then_passes(fixture_data):
    inp = make()  # Ib 30 A, ambient 40 C, 1 circuit
    # 4 mm2: Iz = 33 x 0.87 x 1.00 = 28.71 A < 30 -> FAIL
    c4 = check_current(inp, 4, fixture_data)
    assert c4.actual == pytest.approx(28.71) and not c4.passed
    # 6 mm2: Iz = 43 x 0.87 = 37.41 A >= 30 -> PASS
    c6 = check_current(inp, 6, fixture_data)
    assert c6.actual == pytest.approx(37.41) and c6.passed
    assert c6.unit == "A" and c6.higher_is_better
    assert len(c6.sources) == 3


def test_current_required_is_device_rating_when_larger(fixture_data):
    c = check_current(make(device_rating_a=32), 6, fixture_data)
    assert c.required == 32 and c.passed


def test_current_carries_the_rounding_note(fixture_data):
    # 35 C is not tabulated: the 40 C row is used and the source says so
    c = check_current(make(ambient_c=35), 6, fixture_data)
    assert c.actual == pytest.approx(37.41)
    assert any("35 deg C taken as 40 deg C" in s for s in c.sources)


def test_voltage_drop_three_phase(fixture_data):
    # dU = sqrt(3) x 30 x 0.050 km x (3.3 x 0.8 + 0.09 x 0.6) = 6.9992 V; 6.9992/400 = 1.7498 %
    c = check_voltage_drop(make(), 6, fixture_data)
    assert c.actual == pytest.approx(1.7498, rel=1e-3)
    assert c.passed and c.required == 5 and not c.higher_is_better


def test_voltage_drop_single_phase(fixture_data):
    inp = make(phase="1ph", voltage_v=230, design_current_a=20, power_factor=1.0, length_m=30)
    # dU = 2 x 20 x 0.030 x (8.0 x 1.0 + 0.10 x 0) = 9.6 V; 9.6/230 = 4.1739 %
    c = check_voltage_drop(inp, 2.5, fixture_data)
    assert c.actual == pytest.approx(4.1739, rel=1e-3)


def test_short_circuit(fixture_data):
    # Smin = 2000 x sqrt(0.1) / 115 = 5.4996 mm2
    c5 = check_short_circuit(make(), 4, fixture_data)
    assert c5.required == pytest.approx(5.4996, rel=1e-3) and not c5.passed
    assert check_short_circuit(make(), 6, fixture_data).passed


def test_buried_cable_uses_ground_temperature_and_soil(fixture_data):
    inp = make(method="D2", ambient_c=30, soil_resistivity_kmw=1)
    # Iz = 50 x 0.89 (ground 30 C) x 1.50 (soil 1 K.m/W) x 1.00 = 66.75 A
    c = check_current(inp, 6, fixture_data)
    assert c.actual == pytest.approx(66.75)
    assert "Cs" in c.formula and "Cs = 1.5" in c.detail
    assert len(c.sources) == 4


def test_buried_grouping_says_touching_is_assumed(fixture_data):
    c = check_current(make(method="D2", ambient_c=20, grouped_circuits=2), 6, fixture_data)
    assert any("touching assumed" in s for s in c.sources)


def test_cable_in_air_ignores_soil(fixture_data):
    c = check_current(make(soil_resistivity_kmw=1), 6, fixture_data)
    assert c.actual == pytest.approx(37.41) and len(c.sources) == 3
    assert "Cs" not in c.formula
