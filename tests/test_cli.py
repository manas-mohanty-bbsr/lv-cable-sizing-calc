import shutil
from cablecalc import codes
from cablecalc.cli import main
from tests.conftest import FIXTURE_DIR
from tests.test_io_excel import ROW, filled


def test_template_command(tmp_path):
    out = tmp_path / "t.xlsx"
    assert main(["template", "--out", str(out)]) == 0 and out.exists()


def test_run_command_writes_report(tmp_path, monkeypatch):
    monkeypatch.setattr(codes, "DATA_ROOT", tmp_path / "data")
    shutil.copytree(FIXTURE_DIR, tmp_path / "data" / "iec")
    out = tmp_path / "r.docx"
    assert main(["run", str(filled(tmp_path, [ROW])), "--out", str(out)]) == 0
    assert out.exists()


def test_run_reports_input_errors(tmp_path, capsys):
    bad = filled(tmp_path, [dict(ROW, length_m="x")])
    assert main(["run", str(bad), "--out", str(tmp_path / "r.docx")]) == 2
    assert "field 'length_m' must be a number" in capsys.readouterr().err


def test_run_reports_unsourced_code(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(codes, "DATA_ROOT", tmp_path / "empty")
    assert main(["run", str(filled(tmp_path, [ROW])), "--out", str(tmp_path / "r.docx")]) == 2
    assert "not shipped yet" in capsys.readouterr().err
