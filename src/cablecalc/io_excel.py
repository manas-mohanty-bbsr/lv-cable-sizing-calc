"""Excel in: a blank template, and a reader that reports every problem at once."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from openpyxl import Workbook, load_workbook

from .codes import SUPPORTED_CODES
from .models import CableInput, InputError, design_current_from_kw, validate_input

COLUMNS = ("tag", "phase", "voltage_v", "design_current_a", "load_kw", "power_factor",
           "length_m", "conductor", "insulation", "method", "cores", "ambient_c",
           "grouped_circuits", "vd_limit_pct", "fault_current_ka", "fault_time_s",
           "device_rating_a", "soil_resistivity_kmw")
_TEXT = {"tag", "phase", "conductor", "insulation", "method"}
_INT = {"cores", "grouped_circuits"}
_OPTIONAL = {"design_current_a", "load_kw", "device_rating_a", "soil_resistivity_kmw"}


@dataclass(frozen=True)
class Project:
    name: str
    code: str
    prepared_by: str


def write_template(path: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Project"
    for r, label in enumerate(("Project name", "Code (IEC or IS)", "Prepared by"), start=1):
        ws.cell(r, 1, label)
    cables = wb.create_sheet("Cables")
    cables.append(list(COLUMNS))
    wb.save(path)


def read_input(path: Path) -> tuple[Project, list[CableInput]]:
    wb = load_workbook(path, data_only=True)
    ps = wb["Project"]
    problems: list[str] = []
    code = str(ps["B2"].value or "").strip().upper()
    if code not in SUPPORTED_CODES:
        problems.append(f"Project: field 'code' must be one of {', '.join(SUPPORTED_CODES)}")
    project = Project(str(ps["B1"].value or ""), code, str(ps["B3"].value or ""))

    cables: list[CableInput] = []
    for r, values in enumerate(wb["Cables"].iter_rows(min_row=2, values_only=True), start=2):
        raw = dict(zip(COLUMNS, values))
        if all(v in (None, "") for v in raw.values()):
            continue
        tag = str(raw["tag"] or f"row{r}")
        where = f"Row {r} ({tag})"
        row: dict = {}
        for col in COLUMNS:
            v = raw[col]
            if col in _TEXT:
                row[col] = str(v).strip() if v is not None else ""
                if not row[col]:
                    problems.append(f"{where}: field '{col}' is empty")
            elif v in (None, ""):
                row[col] = None
                if col not in _OPTIONAL:
                    problems.append(f"{where}: field '{col}' is empty")
            else:
                try:
                    row[col] = int(v) if col in _INT else float(v)
                except (TypeError, ValueError):
                    problems.append(f"{where}: field '{col}' must be a number")
                    row[col] = None
        if row.get("design_current_a") is None:
            if row.get("load_kw") is None:
                problems.append(f"{where}: give design_current_a or load_kw")
                continue
            if None in (row.get("voltage_v"), row.get("power_factor")):
                continue
            row["design_current_a"] = design_current_from_kw(
                row["load_kw"], row["voltage_v"], row["power_factor"], row["phase"])
        if any(row[c] is None for c in COLUMNS if c not in _OPTIONAL):
            continue
        row.pop("load_kw")
        if row["soil_resistivity_kmw"] is None:
            row.pop("soil_resistivity_kmw")
        inp = CableInput(**row)
        try:
            validate_input(inp)
        except InputError as e:
            problems.extend(f"Row {r} - {p}" for p in e.problems)
            continue
        cables.append(inp)
    if problems:
        raise InputError(problems)
    return project, cables
