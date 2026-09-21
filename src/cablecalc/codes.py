"""Which standard's tables to use."""
from __future__ import annotations

from pathlib import Path

from .data import CodeData, DataError, load_code_data

SUPPORTED_CODES = ("IEC", "IS")
DATA_ROOT = Path(__file__).parent / "data"


def load_code(code: str) -> CodeData:
    key = code.strip().upper()
    if key not in SUPPORTED_CODES:
        raise DataError(f"Unknown code '{code}'. Use one of: {', '.join(SUPPORTED_CODES)}")
    directory = DATA_ROOT / key.lower()
    if not directory.is_dir():
        raise DataError(f"{key} tables are not shipped yet ({directory} is missing)")
    return load_code_data(directory, key)
