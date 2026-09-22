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


def test_engine_errors_name_every_row(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(codes, "DATA_ROOT", tmp_path / "data")
    shutil.copytree(FIXTURE_DIR, tmp_path / "data" / "iec")
    rows = [dict(ROW, method="B1"), dict(ROW, tag="C2", method="A1")]  # not in the fixture tables
    assert main(["run", str(filled(tmp_path, rows)), "--out", str(tmp_path / "r.docx")]) == 2
    err = capsys.readouterr().err
    assert "Row 2 (C1):" in err and "Row 3 (C2):" in err


def test_report_open_in_word_gives_a_plain_message(tmp_path, monkeypatch, capsys):
    import cablecalc.cli as cli
    monkeypatch.setattr(codes, "DATA_ROOT", tmp_path / "data")
    shutil.copytree(FIXTURE_DIR, tmp_path / "data" / "iec")
    out = tmp_path / "r.docx"

    def locked(path, *a, **k):
        raise PermissionError(13, "Permission denied", str(path))
    monkeypatch.setattr(cli, "write_report", locked)
    assert main(["run", str(filled(tmp_path, [ROW])), "--out", str(out)]) == 2
    err = capsys.readouterr().err
    assert f"Cannot write {out}: it is open in another program" in err
    assert "Traceback" not in err


def test_input_open_elsewhere_gives_a_plain_message(tmp_path, monkeypatch, capsys):
    import cablecalc.cli as cli
    src = filled(tmp_path, [ROW])

    def locked(path):
        raise PermissionError(13, "Permission denied", str(path))
    monkeypatch.setattr(cli, "read_input", locked)
    assert main(["run", str(src), "--out", str(tmp_path / "r.docx")]) == 2
    assert f"Cannot read {src}: it is open in another program" in capsys.readouterr().err


def test_missing_input_gives_a_plain_message(tmp_path, capsys):
    missing = tmp_path / "nope.xlsx"
    assert main(["run", str(missing), "--out", str(tmp_path / "r.docx")]) == 2
    assert f"Cannot find {missing}" in capsys.readouterr().err
