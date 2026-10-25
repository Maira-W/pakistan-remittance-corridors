"""The raw files, the build step and its checks."""

import json
import shutil

import openpyxl
import pandas as pd
import pytest

from remit import build, config, ingest


def test_raw_files_match_the_manifest():
    assert ingest.verify() == []


def test_manifest_records_a_source_and_checksum_for_every_file():
    files = json.loads(config.MANIFEST.read_text(encoding="utf-8"))["files"]
    assert set(files) == {config.ARCHIVE_FILE, config.BULLETIN_FILE}
    for info in files.values():
        assert len(info["sha256"]) == 64 and info["source"].startswith("http") and info["bytes"] > 10_000


def test_workbook_months_are_continuous_and_add_up():
    wide, fy_printed, checks = build.read_workbook()
    assert (str(wide.index.min().date()), str(wide.index.max().date()), len(wide)) == ("2018-07-01", "2024-04-01", 70)
    assert checks["max_gap_leaves_vs_total"] < 0.001
    # SBP's own printed fiscal-year totals, which the months must reproduce
    assert checks["fiscal_years_confirmed_against_sbp_totals"]["FY22"] == pytest.approx(31278.8, abs=0.1)
    assert checks["fiscal_years_confirmed_against_sbp_totals"]["FY23"] == pytest.approx(27332.8, abs=0.1)


def test_corridors_cover_every_dollar():
    wide, _, _ = build.read_workbook()
    long = build.corridor_table(wide)
    by_month = long.groupby("month")["usd_million"].sum()
    assert (by_month - wide["Total"]).abs().max() < 0.001
    assert set(long["corridor"]) == set(config.CORRIDORS) and set(long["region"]) == set(config.REGIONS)


def test_bulletin_table_reproduces_sbp_totals():
    corridor, checks = build.read_bulletin()
    assert corridor["fy26"].sum() == pytest.approx(41584.7, abs=1.0)
    assert corridor["fy25"].sum() == pytest.approx(38299.2, abs=1.0)
    row = corridor.set_index("corridor").loc["USA"]
    assert (row["fy25"], row["fy26"]) == (3720.4, 3623.4)
    assert checks["bulletin_total"]["fy26"] == 41584.7


def test_a_country_that_does_not_add_up_stops_the_build(tmp_path, monkeypatch):
    """Change one country in a copy of the workbook: the build must refuse it, not carry on."""
    raw = tmp_path / "raw"
    shutil.copytree(config.RAW, raw)
    path = raw / config.ARCHIVE_FILE
    wb = openpyxl.load_workbook(path)
    ws = wb[config.ARCHIVE_SHEET]
    for row in ws.iter_rows(min_row=6):
        if row[2].value == "Saudi Arabia":
            row[10].value = row[10].value + 25.0
    wb.save(path)
    monkeypatch.setattr(config, "RAW", raw)
    with pytest.raises(ValueError, match="do not add up"):
        build.read_workbook()


def test_unknown_column_header_is_an_error():
    with pytest.raises(ValueError):
        build._month_of("Q3 2021")
    assert build._month_of("Mar-24R")[0] == pd.Timestamp(2024, 3, 1)
    assert build._month_of("FY22")[1] == "FY22"


def test_committed_tables_are_what_the_raw_files_produce(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "INTERIM", tmp_path)
    build.run()
    for name in ("monthly_by_corridor.csv", "annual_by_corridor_bulletin.csv", "monthly_by_sbp_row.csv"):
        fresh = pd.read_csv(tmp_path / name)
        committed = pd.read_csv(config.ROOT / "data" / "interim" / name)
        pd.testing.assert_frame_equal(fresh, committed, check_exact=False, atol=1e-6)
