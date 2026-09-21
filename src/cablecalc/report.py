"""Word out: a formal calculation sheet. Plain text only - no emoji, arrows or middots."""
from __future__ import annotations

from pathlib import Path

from docx import Document

from . import __version__
from .io_excel import Project
from .models import SizingResult

CHECK_LABELS = {
    "current": "Current-carrying capacity",
    "voltage_drop": "Voltage drop",
    "short_circuit": "Short-circuit withstand",
}

GOVERNING_NOTE = ("Governing check: the check that the next smaller size fails (the one failing by the "
                  "widest margin, if more than one does). A dash means the smallest size in the table "
                  "already passes.")

LIMITATIONS = (
    "Low-voltage cables up to 1.1 kV only.",
    "Only the installation methods and sizes present in the shipped tables are supported. An ambient "
    "temperature, number of grouped circuits or soil thermal resistivity between tabulated rows takes "
    "the next higher row, as stated in the Sources line; values are never interpolated.",
    "For buried cables (methods D1 and D2) the ambient temperature is the ground temperature, and "
    "grouping assumes the cables or ducts are touching.",
    "Harmonic derating and protective device coordination are not calculated.",
    "This is a sample tool, not a design service. Results must be checked by a qualified engineer.",
)


def _table(doc, rows):
    t = doc.add_table(rows=0, cols=len(rows[0]))
    t.style = "Table Grid"
    for row in rows:
        cells = t.add_row().cells
        for c, v in zip(cells, row):
            c.text = str(v)
    return t


def write_report(path: Path, project: Project, results: list[SizingResult], today: str) -> None:
    doc = Document()
    doc.add_heading("LV Cable Sizing Calculation", level=0)
    _table(doc, [("Project", project.name), ("Date", today), ("Code", project.code),
                 ("Tool version", f"cablecalc {__version__}"),
                 ("Prepared by", project.prepared_by)])
    doc.add_paragraph(f"Code: {project.code}")
    doc.add_paragraph("Checked by: ____________________")

    for res in results:
        doc.add_heading(f"Cable {res.tag}", level=1)
        doc.add_paragraph(res.message)
        for c in res.checks:
            doc.add_heading(CHECK_LABELS[c.name], level=2)
            _table(doc, [
                ("Formula", c.formula),
                ("Values", c.detail),
                ("Required", f"{c.required:.4g} {c.unit}"),
                ("Actual", f"{c.actual:.4g} {c.unit}"),
                ("Result", "PASS" if c.passed else "FAIL"),
                ("Sources", "; ".join(c.sources)),
            ])

    doc.add_heading("Summary", level=1)
    _table(doc, [("Cable", "Size (mm2)", "Governing check", "Result")] + [
        (r.tag, f"{r.size_mm2:g}" if r.size_mm2 else "-",
         CHECK_LABELS[r.governing] if r.governing else "-",
         "PASS" if r.passed else "FAIL") for r in results])
    doc.add_paragraph(GOVERNING_NOTE)

    doc.add_heading("Limitations", level=1)
    for line in LIMITATIONS:
        doc.add_paragraph(line)
    doc.save(path)
