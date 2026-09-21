import pytest
from cablecalc.models import (CableInput, CheckResult, InputError,
                              design_current_from_kw, validate_input)


def make(**overrides):
    base = dict(tag="C1", phase="3ph", voltage_v=400, design_current_a=30,
                power_factor=0.8, length_m=50, conductor="Cu", insulation="PVC",
                method="C", cores=3, ambient_c=40, grouped_circuits=1,
                vd_limit_pct=5, fault_current_ka=2, fault_time_s=0.1)
    base.update(overrides)
    return CableInput(**base)


def test_valid_input_passes():
    validate_input(make())


@pytest.mark.parametrize("field,value,reason", [
    ("phase", "2ph", "must be '1ph' or '3ph'"),
    ("length_m", 0, "must be greater than 0"),
    ("power_factor", 1.2, "must be between 0 and 1"),
    ("fault_time_s", -1, "must be greater than 0"),
    ("grouped_circuits", 0, "must be 1 or more"),
    ("conductor", "Fe", "must be 'Cu' or 'Al'"),
    ("insulation", "EPR", "must be 'PVC' or 'XLPE'"),
])
def test_invalid_field_is_named(field, value, reason):
    with pytest.raises(InputError) as exc:
        validate_input(make(**{field: value}))
    assert f"C1: field '{field}' {reason}" in exc.value.problems


def test_all_problems_reported_together():
    with pytest.raises(InputError) as exc:
        validate_input(make(length_m=0, fault_time_s=0))
    assert len(exc.value.problems) == 2


def test_design_current_three_phase():
    # I = P / (sqrt(3) x U x pf) = 22000 / (1.7320508 x 400 x 0.8) = 39.69 A
    assert design_current_from_kw(22, 400, 0.8, "3ph") == pytest.approx(39.6928, rel=1e-4)


def test_design_current_single_phase():
    # I = P / (U x pf) = 2300 / (230 x 1.0) = 10 A
    assert design_current_from_kw(2.3, 230, 1.0, "1ph") == pytest.approx(10.0)


def test_margin_higher_is_better():
    c = CheckResult("current", True, 30, 37.41, "A", True, "", (), "")
    assert c.margin == pytest.approx(37.41 / 30)


def test_margin_lower_is_better():
    c = CheckResult("voltage_drop", True, 5.0, 2.0, "%", False, "", (), "")
    assert c.margin == pytest.approx(2.5)


def test_soil_resistivity_defaults_to_the_table_reference():
    assert make().soil_resistivity_kmw == 2.5


def test_soil_resistivity_must_be_positive():
    with pytest.raises(InputError, match="soil_resistivity_kmw"):
        validate_input(make(soil_resistivity_kmw=0))
