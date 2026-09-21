import pytest
from cablecalc.codes import SUPPORTED_CODES, load_code
from cablecalc.data import DataError


def test_supported_codes():
    assert SUPPORTED_CODES == ("IEC", "IS")


def test_unknown_code_is_refused():
    with pytest.raises(DataError, match="Unknown code 'BS'. Use one of: IEC, IS"):
        load_code("BS")


def test_code_is_case_insensitive_and_named(monkeypatch, tmp_path):
    import shutil
    from cablecalc import codes
    from tests.conftest import FIXTURE_DIR
    monkeypatch.setattr(codes, "DATA_ROOT", tmp_path)
    shutil.copytree(FIXTURE_DIR, tmp_path / "iec")
    assert load_code("iec").code == "IEC"


def test_missing_data_dir_says_not_yet_sourced(monkeypatch, tmp_path):
    from cablecalc import codes
    monkeypatch.setattr(codes, "DATA_ROOT", tmp_path)
    with pytest.raises(DataError, match="IS tables are not shipped yet"):
        load_code("IS")
