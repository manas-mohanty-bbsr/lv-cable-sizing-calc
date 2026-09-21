import shutil
import pytest
from cablecalc.data import DataError, load_code_data
from tests.conftest import FIXTURE_DIR


def test_lookups_return_value_and_source(fixture_data):
    amps, src = fixture_data.ampacity("Cu", "PVC", "C", 3, 6)
    assert amps == 43 and src.startswith("TEST FIXTURE")
    assert fixture_data.temp_factor("PVC", 40)[0] == 0.87
    assert fixture_data.group_factor("C", 2)[0] == 0.80
    r, x, _ = fixture_data.impedance("Cu", "PVC", 10)
    assert (r, x) == (2.0, 0.09)
    assert fixture_data.k_factor("Cu", "PVC")[0] == 115


def test_sizes_ascending(fixture_data):
    assert fixture_data.sizes("Cu", "PVC", "C", 3) == [2.5, 4, 6, 10, 16]


def test_missing_value_names_the_key(fixture_data):
    with pytest.raises(DataError, match="ampacity.*size_mm2=25"):
        fixture_data.ampacity("Cu", "PVC", "C", 3, 25)
    with pytest.raises(DataError, match="group_factor.*method=E"):
        fixture_data.group_factor("E", 1)


def test_exact_match_carries_no_note(fixture_data):
    factor, src = fixture_data.temp_factor("PVC", 40)
    assert factor == 0.87 and "taken as" not in src


def test_ambient_between_rows_takes_the_hotter_row(fixture_data):
    # never interpolated: the more severe tabulated value is used, and the source says so
    factor, src = fixture_data.temp_factor("PVC", 35)
    assert factor == 0.87
    assert src.endswith("(35 deg C taken as 40 deg C, next higher tabulated value)")


def test_ambient_below_table_takes_the_lowest_row(fixture_data):
    factor, src = fixture_data.temp_factor("PVC", 20)
    assert factor == 1.00
    assert "20 deg C taken as 30 deg C" in src


def test_ambient_above_table_is_refused(fixture_data):
    with pytest.raises(DataError, match="ambient_c=45 .*above the highest tabulated value 40"):
        fixture_data.temp_factor("PVC", 45)


def test_circuits_between_rows_take_the_larger_group(fixture_data):
    factor, src = fixture_data.group_factor("C", 3)
    assert factor == 0.65
    assert src.endswith("(3 circuits taken as 4, next higher tabulated value)")


def test_circuits_above_table_are_refused(fixture_data):
    with pytest.raises(DataError, match="circuits=5 .*above the highest tabulated value 4"):
        fixture_data.group_factor("C", 5)


def test_rounded_value_is_never_interpolated(fixture_data):
    # 35 deg C lies between 1.00 and 0.87; any value strictly between would mean interpolation
    assert fixture_data.temp_factor("PVC", 35)[0] in (1.00, 0.87)


def test_row_without_source_is_refused(tmp_path):
    for f in FIXTURE_DIR.glob("*.csv"):
        shutil.copy(f, tmp_path / f.name)
    (tmp_path / "k_factor.csv").write_text(
        "conductor,insulation,k,source\nCu,PVC,115,\n", encoding="utf-8")
    with pytest.raises(DataError, match="k_factor.csv row 2: empty source"):
        load_code_data(tmp_path, "X")


def test_missing_file_is_refused(tmp_path):
    with pytest.raises(DataError, match="ampacity.csv not found"):
        load_code_data(tmp_path, "X")


def test_wrong_header_is_refused(tmp_path):
    for f in FIXTURE_DIR.glob("*.csv"):
        shutil.copy(f, tmp_path / f.name)
    (tmp_path / "k_factor.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    with pytest.raises(DataError, match="k_factor.csv: expected columns"):
        load_code_data(tmp_path, "X")
