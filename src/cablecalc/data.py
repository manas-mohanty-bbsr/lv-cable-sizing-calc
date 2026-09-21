"""Per-standard lookup tables. Every row must name its source.

Sizes, impedances and k factors are exact match only. Ambient temperature and number of
grouped circuits take the next higher tabulated row (the more severe case) and say so in
the returned source. Nothing is ever interpolated.
"""
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

    def _find_or_next_higher(self, name: str, var: str, value, **key):
        """Exact row, else the row with the next higher `var` (the more severe case).

        Never interpolates. Returns (row, used_value); used_value is None on an exact match.
        A value above the highest tabulated one is refused.
        """
        shown = ", ".join(f"{k}={v}" for k, v in key.items())
        rows = [r for r in self.tables[name] if all(r[k] == v for k, v in key.items())]
        if not rows:
            raise DataError(f"{self.code} {name}: no rows for {shown}")
        for r in rows:
            if r[var] == value:
                return r, None
        higher = [r for r in rows if r[var] > value]
        if not higher:
            top = max(r[var] for r in rows)
            raise DataError(f"{self.code} {name}: {var}={value:g} for {shown} is above "
                            f"the highest tabulated value {top:g}")
        r = min(higher, key=lambda row: row[var])
        return r, r[var]

    def temp_factor(self, insulation, ambient_c):
        ambient_c = float(ambient_c)
        r, used = self._find_or_next_higher("temp_factor", "ambient_c", ambient_c,
                                            insulation=insulation)
        if used is None:
            return r["factor"], r["source"]
        return r["factor"], (f"{r['source']} ({ambient_c:g} deg C taken as {used:g} deg C, "
                             f"next higher tabulated value)")

    def group_factor(self, method, circuits):
        circuits = int(circuits)
        r, used = self._find_or_next_higher("group_factor", "circuits", circuits, method=method)
        if used is None:
            return r["factor"], r["source"]
        return r["factor"], (f"{r['source']} ({circuits} circuits taken as {used}, "
                             f"next higher tabulated value)")

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
