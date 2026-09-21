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
    with pytest.raises(DataError, match="group_factor.*method=C.*circuits=3"):
        fixture_data.group_factor("C", 3)


def test_no_interpolation(fixture_data):
    with pytest.raises(DataError, match="ambient_c=35"):
        fixture_data.temp_factor("PVC", 35)


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
