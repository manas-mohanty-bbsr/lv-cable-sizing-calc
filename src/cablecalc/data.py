"""Per-standard lookup tables. Exact match only; every row must name its source."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


class DataError(ValueError):
    pass


_SPEC = {
    "ampacity": (("conductor", "insulation", "method", "cores", "size_mm2", "amps", "source"),
                 {"cores": int, "size_mm2": float, "amps": float}),
    "temp_factor": (("insulation", "ambient_c", "factor", "source"),
                    {"ambient_c": float, "factor": float}),
    "group_factor": (("method", "circuits", "factor", "source"),
                     {"circuits": int, "factor": float}),
    "impedance": (("conductor", "insulation", "size_mm2", "r_ohm_per_km", "x_ohm_per_km", "source"),
                  {"size_mm2": float, "r_ohm_per_km": float, "x_ohm_per_km": float}),
    "k_factor": (("conductor", "insulation", "k", "source"), {"k": float}),
}


def _load(directory: Path, name: str) -> list[dict]:
    path = directory / f"{name}.csv"
    if not path.exists():
        raise DataError(f"{name}.csv not found in {directory}")
    columns, types = _SPEC[name]
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if tuple(reader.fieldnames or ()) != columns:
            raise DataError(f"{name}.csv: expected columns {','.join(columns)}")
        rows = []
        for i, raw in enumerate(reader, start=2):
            if not (raw.get("source") or "").strip():
                raise DataError(f"{name}.csv row {i}: empty source")
            row = dict(raw)
            for col, typ in types.items():
                try:
                    row[col] = typ(raw[col])
                except (TypeError, ValueError):
                    raise DataError(f"{name}.csv row {i}: {col}={raw[col]!r} is not a number")
            rows.append(row)
    return rows


@dataclass(frozen=True)
class CodeData:
    code: str
    tables: dict

    def _find(self, name: str, **key):
        for row in self.tables[name]:
            if all(row[k] == v for k, v in key.items()):
                return row
        shown = ", ".join(f"{k}={v}" for k, v in key.items())
        raise DataError(f"{self.code} {name}: no row for {shown}")

    def ampacity(self, conductor, insulation, method, cores, size_mm2):
        r = self._find("ampacity", conductor=conductor, insulation=insulation,
                       method=method, cores=cores, size_mm2=float(size_mm2))
        return r["amps"], r["source"]

    def temp_factor(self, insulation, ambient_c):
        r = self._find("temp_factor", insulation=insulation, ambient_c=float(ambient_c))
        return r["factor"], r["source"]

    def group_factor(self, method, circuits):
        r = self._find("group_factor", method=method, circuits=int(circuits))
        return r["factor"], r["source"]

    def impedance(self, conductor, insulation, size_mm2):
        r = self._find("impedance", conductor=conductor, insulation=insulation,
                       size_mm2=float(size_mm2))
        return r["r_ohm_per_km"], r["x_ohm_per_km"], r["source"]

    def k_factor(self, conductor, insulation):
        r = self._find("k_factor", conductor=conductor, insulation=insulation)
        return r["k"], r["source"]

    def sizes(self, conductor, insulation, method, cores):
        found = sorted({r["size_mm2"] for r in self.tables["ampacity"]
                        if (r["conductor"], r["insulation"], r["method"], r["cores"])
                        == (conductor, insulation, method, cores)})
        if not found:
            raise DataError(f"{self.code} ampacity: no sizes for conductor={conductor}, "
                            f"insulation={insulation}, method={method}, cores={cores}")
        return found


def load_code_data(directory: Path, code: str) -> CodeData:
    directory = Path(directory)
    return CodeData(code, {name: _load(directory, name) for name in _SPEC})
