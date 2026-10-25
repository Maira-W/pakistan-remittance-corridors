"""The analysis on cases with known answers, and the committed results."""

import json
from datetime import date

import numpy as np
import pandas as pd
import pytest

from remit import analysis, config


def test_a_flat_series_has_a_ratio_of_one():
    s = pd.Series(5.0, index=pd.date_range("2020-01-01", periods=36, freq="MS"))
    d = analysis.detrend(s)
    assert d["ratio"].dropna().round(9).eq(1.0).all()
    assert d["ratio"].notna().sum() == 36 - 12          # six months lost at each end


def test_window_shares_split_a_window_across_months():
    # Eid on 3 May 2022: the 21 days before it are 12 April to 2 May
    april, may = pd.Timestamp("2022-04-01"), pd.Timestamp("2022-05-01")
    assert analysis.before_share(april, [date(2022, 5, 3)]) == pytest.approx(19 / 21)
    assert analysis.before_share(may, [date(2022, 5, 3)]) == pytest.approx(2 / 21)
    assert analysis.before_share(pd.Timestamp("2022-06-01"), [date(2022, 5, 3)]) == 0
    assert analysis.after_share(may, [date(2022, 5, 3)]) == pytest.approx(1.0)     # 4 to 24 May, all inside May


def test_the_model_recovers_an_eid_effect_that_was_put_in():
    index = pd.date_range(config.FIRST_MONTH, "2024-04-01", freq="MS")
    f = analysis.eid_features(index)
    rng = np.random.default_rng(config.SEED)
    log_ratio = 0.10 * f["before_eid"] + rng.normal(0, 0.01, len(index))
    got = analysis.eid_effects(log_ratio)["pooled"]["before_eid"]
    assert got["coef"] == pytest.approx(0.10, abs=0.02)
    assert got["lo_pct"] < np.expm1(0.10) * 100 < got["hi_pct"]
    # and the shifted calendars of the placebo test should not find an effect that large
    pl = analysis.placebo(log_ratio)
    assert (pl["uplift_pct"] >= got["uplift_pct"]).mean() < 0.05


def test_no_effect_is_not_found_in_noise():
    index = pd.date_range(config.FIRST_MONTH, "2024-04-01", freq="MS")
    noise = pd.Series(np.random.default_rng(1).normal(0, 0.05, len(index)), index=index)
    got = analysis.eid_effects(noise)["pooled"]["before_eid"]
    assert got["lo_pct"] < 0 < got["hi_pct"]


def test_hhi_is_one_over_n_when_shares_are_equal_and_one_when_alone():
    assert analysis.hhi(pd.Series([1, 1, 1, 1])) == pytest.approx(0.25)
    assert analysis.hhi(pd.Series([5, 0, 0])) == 1


def test_tiers_follow_the_cut_offs():
    s = pd.DataFrame({"corridor": ["A", "B", "C", "D"], "share_fy26_pct": [60, 7, 0.9, 5],
                      "fy26_usd_m": [6000, 700, 90, 600], "fy25_usd_m": [5900, 500, 80, 600], "growth_fy26_pct": [1.7, 40, 12, 0]})
    t = analysis.tiers(s).set_index("corridor")
    assert t.loc["A", "tier"].startswith("Tier 1") and t.loc["B", "tier"].startswith("Tier 2") and t.loc["C", "tier"].startswith("Tier 3")
    assert bool(t.loc["B", "fast_riser"]) and not bool(t.loc["D", "fast_riser"]) and not bool(t.loc["A", "fast_riser"])


def test_shares_add_to_one_hundred(corridors):
    assert corridors["share_fy26_pct"].sum() == pytest.approx(100)
    assert corridors["share_fy20_pct"].sum() == pytest.approx(100)
    regions = pd.read_csv(config.PROCESSED / "region_share_by_fiscal_year.csv").set_index("fiscal_year")
    assert regions.sum(axis=1).sub(100).abs().max() < 1e-3


def test_results_agree_with_the_inputs(summary, corridors, annual):
    assert corridors["fy26_usd_m"].sum() == pytest.approx(annual["fy26"].sum())
    assert summary["fy_totals_usd_m"]["FY26"] == pytest.approx(41584.7, abs=1.0)
    assert summary["months_used"] == ["2019-07-01", "2024-04-01", 58]
    assert summary["months_with_trend"] == 46
    assert summary["tier1"] == ["Saudi Arabia", "UAE", "UK", "USA"]
    assert not set(summary["fast_risers"]) & set(config.AGGREGATES)


def test_eid_estimates_are_internally_consistent(summary):
    e = summary["eid"]["pooled"]["before_eid"]
    assert e["lo_pct"] < e["uplift_pct"] < e["hi_pct"]
    pl = summary["placebo"]
    assert 0 < pl["share_of_shifts_as_large"] < 1
    assert pl["rank_of_real"] == round(pl["share_of_shifts_as_large"] * pl["n_shifts"]) + 1


def test_analysis_is_reproducible(tmp_path, monkeypatch, summary):
    monkeypatch.setattr(config, "PROCESSED", tmp_path)
    analysis.run()
    fresh = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert fresh["eid"]["pooled"]["before_eid"]["uplift_pct"] == pytest.approx(summary["eid"]["pooled"]["before_eid"]["uplift_pct"], abs=1e-6)
    for name in ("corridor_summary.csv", "seasonal_index.csv", "planning_calendar.csv"):
        pd.testing.assert_frame_equal(pd.read_csv(tmp_path / name), pd.read_csv(config.ROOT / "data" / "processed" / name),
                                      check_exact=False, atol=1e-6)


def test_calendar_ranges_are_ordered_and_windows_add_up():
    cal = pd.read_csv(config.PROCESSED / "planning_calendar.csv")
    for _, r in cal.iterrows():
        assert r["low_uplift_pct"] <= r["central_uplift_pct"] <= r["high_uplift_pct"]
    assert set(cal["event"]) == set(config.NEXT_EIDS)
    assert cal.groupby("event")["share_of_window_in_month"].sum().round(2).eq(1.0).all()
