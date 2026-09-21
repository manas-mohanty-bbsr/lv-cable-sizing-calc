"""cablecalc template --out input.xlsx | cablecalc run input.xlsx --out report.docx"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from . import codes
from .core import size_cable
from .data import DataError
from .io_excel import read_input, write_template
from .models import InputError
from .report import write_report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="cablecalc")
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("template", help="write a blank input workbook")
    t.add_argument("--out", required=True, type=Path)
    r = sub.add_parser("run", help="size every cable and write the report")
    r.add_argument("input", type=Path)
    r.add_argument("--out", required=True, type=Path)
    args = ap.parse_args(argv)

    if args.cmd == "template":
        write_template(args.out)
        print(f"Template written: {args.out}")
        return 0
    try:
        project, cables = read_input(args.input)
        data = codes.load_code(project.code)
        results = [size_cable(c, data) for c in cables]
    except (InputError, DataError) as e:
        problems = getattr(e, "problems", [str(e)])
        print("Cannot run:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 2
    write_report(args.out, project, results, today=date.today().isoformat())
    print(f"Report written: {args.out} ({len(results)} cables)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
