import pytest
from cablecalc.codes import SUPPORTED_CODES, load_code


@pytest.mark.parametrize("code", SUPPORTED_CODES)
def test_shipped_tables_load_with_real_sources(code):
    data = load_code(code)
    for name, rows in data.tables.items():
        assert rows, f"{code} {name} is empty"
        for row in rows:
            assert "TEST FIXTURE" not in row["source"], f"{code} {name} ships fixture data"


# Spot values, each read from the printed table named in the test.
@pytest.mark.parametrize("code", SUPPORTED_CODES)
@pytest.mark.parametrize("args,amps", [
    (("Cu", "PVC", "C", 3, 25), 96),      # IS 732 Table 23 / IEC B.52.4
    (("Al", "XLPE", "D2", 3, 300), 326),  # IS 732 Table 24 / IEC B.52.5
    (("Cu", "PVC", "A1", 2, 1.5), 14.5),  # IS 732 Table 21 / IEC B.52.2
    (("Cu", "XLPE", "E", 3, 240), 538),   # IS 732 Table 31 / IEC B.52.12
])
def test_spot_ampacity(code, args, amps):
    assert load_code(code).ampacity(*args)[0] == amps


@pytest.mark.parametrize("code", SUPPORTED_CODES)
def test_spot_factors(code):
    data = load_code(code)
    assert data.temp_factor("PVC", 40)[0] == 0.87                    # Table 33
    assert data.temp_factor("XLPE", 30, medium="ground")[0] == 0.93  # Table 34
    assert data.soil_factor("D2", 1)[0] == 1.5                       # Table 35
    assert data.group_factor("C", 3)[0] == 0.79                      # Table 36 item 2
    assert data.group_factor("D1", 4)[0] == 0.70                     # Table 38 A
    assert data.k_factor("Al", "XLPE")[0] == 94                      # IS 732 Table 3


@pytest.mark.parametrize("code", SUPPORTED_CODES)
def test_resistance_follows_the_annex_y_method(code):
    r, x, _ = load_code(code).impedance("Cu", "PVC", 10)
    assert r == pytest.approx(2.25) and x == 0.08    # 0.0225 ohm.mm2/m / 10 mm2


def test_d2_aluminium_starts_at_16_mm2():
    # The standard gives no direct-buried rating for Al below 16 mm2; nothing is filled in.
    assert load_code("IS").sizes("Al", "PVC", "D2", 3)[0] == 16
