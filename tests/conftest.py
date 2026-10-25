import json

import pandas as pd
import pytest

from remit import analysis, config


@pytest.fixture(scope="session")
def summary():
    return json.loads((config.PROCESSED / "summary.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def monthly():
    return analysis.load()[0]


@pytest.fixture(scope="session")
def annual():
    return analysis.load()[1]


@pytest.fixture(scope="session")
def corridors():
    return pd.read_csv(config.PROCESSED / "corridor_summary.csv")
