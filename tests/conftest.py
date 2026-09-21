from pathlib import Path
import pytest
from cablecalc.data import load_code_data

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "tables"


@pytest.fixture
def fixture_data():
    return load_code_data(FIXTURE_DIR, "FIXTURE")
