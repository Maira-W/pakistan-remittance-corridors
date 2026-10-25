"""The analysis: where the money comes from, how that is changing, and when it arrives.

Three questions, each answered from the tables that `remit build` wrote:

1. Corridors. How big is each country's flow, how fast is it growing, and how concentrated is the whole?
2. Seasonality. How much higher are remittances in the weeks before Eid, after taking out the long-run trend?
3. Priorities. Which corridors would a new remittance product serve first, and when should it plan extra capacity?
"""

from __future__ import annotations

import json
from datetime import date, timedelta

import numpy as np
import pandas as pd
import statsmodels.api as sm

from . import config

FY_FULL = {"FY20": ("2019-07-01", "2020-06-01"), "FY21": ("2020-07-01", "2021-06-01"),
           "FY22": ("2021-07-01", "2022-06-01"), "FY23": ("2022-07-01", "2023-06-01")}


# ---------------------------------------------------------------------------
# Corridors
# ---------------------------------------------------------------------------
def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    monthly = pd.read_csv(config.INTERIM / "monthly_by_corridor.csv", parse_dates=["month"])
    annual = pd.read_csv(config.INTERIM / "annual_by_corridor_bulletin.csv")
    return monthly[monthly["month"] >= config.FIRST_MONTH].copy(), annual


def hhi(values: pd.Series) -> float:
    """Herfindahl index of shares, 0 to 1: 1/n when every corridor is equal, 1 when one corridor has everything."""
    shares = values / values.sum()
    return float((shares ** 2).sum())


def fiscal_years(monthly: pd.DataFrame, annual: pd.DataFrame) -> pd.DataFrame:
    """Million US dollars by corridor for FY20 to FY23 (from the monthly workbook) and FY25 and FY26 (from the bulletin).

    FY24 is missing at country level: the workbook ends in April 2024 and the bulletin starts at FY25, so the
    growth comparison for FY24 uses the same ten months (July to April) in every year instead.
    """
    wide = monthly.pivot(index="month", columns="corridor", values="usd_million")
    out = pd.DataFrame({fy: wide.loc[a:b].sum() for fy, (a, b) in FY_FULL.items()})
    out["FY25"] = annual.set_index("corridor")["fy25"]
    out["FY26"] = annual.set_index("corridor")["fy26"]
    return out.loc[config.CORRIDORS]


def ten_month_window(monthly: pd.DataFrame) -> pd.DataFrame:
    """July to April totals for FY20 to FY24, the one window the workbook covers in every year."""
    wide = monthly.pivot(index="month", columns="corridor", values="usd_million")
    out = {f"FY{y % 100}": wide.loc[f"{y - 1}-07-01":f"{y}-04-01"].sum() for y in range(2020, 2025)}
    return pd.DataFrame(out).loc[config.CORRIDORS]


def corridor_summary(fy: pd.DataFrame, window: pd.DataFrame) -> pd.DataFrame:
    s = pd.DataFrame(index=fy.index)
    s["region"] = [config.CORRIDOR_REGION[c] for c in s.index]
    s["fy23_usd_m"] = fy["FY23"]
    s["fy25_usd_m"] = fy["FY25"]
    s["fy26_usd_m"] = fy["FY26"]
    s["share_fy26_pct"] = fy["FY26"] / fy["FY26"].sum() * 100
    s["share_fy20_pct"] = fy["FY20"] / fy["FY20"].sum() * 100
    s["growth_fy26_pct"] = (fy["FY26"] / fy["FY25"] - 1) * 100
    s["added_fy26_usd_m"] = fy["FY26"] - fy["FY25"]
    s["share_of_growth_pct"] = s["added_fy26_usd_m"] / s["added_fy26_usd_m"].sum() * 100
    s["cagr_window_fy20_fy24_pct"] = ((window["FY24"] / window["FY20"]) ** (1 / 4) - 1) * 100
    s.index.name = "corridor"
    return s.reset_index().sort_values("fy26_usd_m", ascending=False).reset_index(drop=True)


def region_shares(fy: pd.DataFrame) -> pd.DataFrame:
    by_region = fy.groupby(pd.Series(config.CORRIDOR_REGION)).sum()
    return (by_region / by_region.sum() * 100).loc[config.REGIONS].T.rename_axis("fiscal_year").reset_index()


def tiers(summary: pd.DataFrame) -> pd.DataFrame:
    """Tier 1: at least 8% of FY26 inflows. Tier 2: 1% to 8%. Tier 3: under 1%. The two groups of small countries get no tier.

    A fast riser is a single country outside tier 1, worth at least 500 million dollars, whose FY26 growth beats the whole
    by ten points or more. The two groups of small countries are not counted: a provider cannot serve "other countries".
    """
    s = summary.copy()
    s["tier"] = np.select([s["share_fy26_pct"] >= 8, s["share_fy26_pct"] >= 1], ["Tier 1: core", "Tier 2: build"], "Tier 3: watch")
    s.loc[s["corridor"].isin(config.AGGREGATES), "tier"] = "Group of small countries"
    total_growth = (s["fy26_usd_m"].sum() / s["fy25_usd_m"].sum() - 1) * 100
    s["fast_riser"] = ((s["tier"] != "Tier 1: core") & (s["growth_fy26_pct"] >= total_growth + 10) & (s["fy26_usd_m"] >= 500)
                       & ~s["corridor"].isin(config.AGGREGATES))
    return s


# ---------------------------------------------------------------------------
# Seasonality
# ---------------------------------------------------------------------------
def detrend(per_day: pd.Series) -> pd.DataFrame:
    """Divide each month's daily average by a centred 12-month moving average (the ratio-to-moving-average method).

    A twelve-month average removes the long-run level and any pattern that repeats every year, and loses six months at
    each end of the series. Daily averages keep February from looking weak just because it is short.
    """
    ma = per_day.rolling(12, center=True).mean()
    trend = ma.rolling(2).mean().shift(-1)                       # centre the even-length window
    ratio = per_day / trend
    return pd.DataFrame({"usd_m_per_day": per_day, "trend": trend, "ratio": ratio, "log_ratio": np.log(ratio)})


def _days(month_start: pd.Timestamp) -> list[date]:
    return list(pd.date_range(month_start, month_start + pd.offsets.MonthEnd(0)).date)


def before_share(month_start: pd.Timestamp, eids: list[date], n: int = config.EID_WINDOW_DAYS) -> float:
    """Share of the n days before each Eid that fall in this month, summed over the Eids (a whole window gives 1)."""
    return sum(1 for eid in eids for d in _days(month_start) if eid - timedelta(days=n) <= d < eid) / n


def after_share(month_start: pd.Timestamp, eids: list[date], n: int = config.EID_WINDOW_DAYS) -> float:
    return sum(1 for eid in eids for d in _days(month_start) if eid < d <= eid + timedelta(days=n)) / n


def eid_features(index: pd.DatetimeIndex, shift_days: int = 0) -> pd.DataFrame:
    """For each month: how much of the 21 days before each Eid, and of the 21 days after both, it contains."""
    fitr = [d + timedelta(days=shift_days) for d in config.EID_AL_FITR]
    adha = [d + timedelta(days=shift_days) for d in config.EID_AL_ADHA]
    f = pd.DataFrame({"before_fitr": [before_share(m, fitr) for m in index],
                      "before_adha": [before_share(m, adha) for m in index],
                      "after_eid": [after_share(m, fitr + adha) for m in index]}, index=index)
    f["before_eid"] = f["before_fitr"] + f["before_adha"]
    return f


def _fit(y: pd.Series, X: pd.DataFrame) -> dict:
    fit = sm.OLS(y, sm.add_constant(X)).fit(cov_type="HC3")
    ci = fit.conf_int()
    out = {"n": int(len(y)), "r2": float(fit.rsquared)}
    for name in X.columns:
        out[name] = {"coef": float(fit.params[name]), "se": float(fit.bse[name]), "p": float(fit.pvalues[name]),
                     "uplift_pct": float(np.expm1(fit.params[name]) * 100),
                     "lo_pct": float(np.expm1(ci.loc[name, 0]) * 100), "hi_pct": float(np.expm1(ci.loc[name, 1]) * 100)}
    return out


def eid_effects(log_ratio: pd.Series, shift_days: int = 0) -> dict:
    """OLS of the detrended log level on the Eid windows, with heteroskedasticity-robust (HC3) errors.

    `pooled` treats both Eids alike (the main result: more data behind one number); `separate` lets them differ.
    """
    y = log_ratio.dropna()
    f = eid_features(y.index, shift_days)
    return {"pooled": _fit(y, f[["before_eid", "after_eid"]]), "separate": _fit(y, f[["before_fitr", "before_adha", "after_eid"]])}


def placebo(log_ratio: pd.Series) -> pd.DataFrame:
    """Move every Eid by the same number of days (-150 to +150) and refit the pooled model.

    If the pre-Eid uplift were noise, shifted calendars would often find uplifts as big as the real one. The real
    calendar's rank among the shifts says how unusual it is.
    """
    rows = []
    for k in range(-150, 151, 3):
        if abs(k) < 9:
            continue                                   # windows still overlap the real ones
        rows.append({"shift_days": k, "uplift_pct": eid_effects(log_ratio, k)["pooled"]["before_eid"]["uplift_pct"]})
    return pd.DataFrame(rows)


def seasonal_index(frame: pd.DataFrame) -> pd.DataFrame:
    d = frame.dropna(subset=["ratio"]).copy()
    d["calendar_month"] = d.index.month
    g = d.groupby("calendar_month")["ratio"].agg(["mean", "std", "count"])
    g.columns = ["index", "sd", "years"]
    g["index_pct_vs_trend"] = (g["index"] - 1) * 100
    return g.reset_index()


def corridor_seasonality(monthly: pd.DataFrame) -> pd.DataFrame:
    wide = monthly.pivot(index="month", columns="corridor", values="usd_million")
    rows = []
    sizes = wide.drop(columns=config.AGGREGATES).sum().sort_values(ascending=False)
    for corridor in sizes.index[:config.N_MAJOR]:
        s = wide[corridor] / wide.index.days_in_month
        r = eid_effects(detrend(s)["log_ratio"])["pooled"]
        e = r["before_eid"]
        rows.append({"corridor": corridor, "n": r["n"], "uplift_pct": e["uplift_pct"], "lo_pct": e["lo_pct"], "hi_pct": e["hi_pct"], "p": e["p"]})
    return pd.DataFrame(rows)


def planning_calendar(effect: dict, monthly_level: float) -> pd.DataFrame:
    """Indicative extra money against trend in each calendar month the next two pre-Eid windows touch.

    The range comes from the 95% interval of the pooled estimate, so it is wide: it is a planning range, not a forecast.
    """
    rows = []
    n = config.EID_WINDOW_DAYS
    for name, eid in config.NEXT_EIDS.items():
        start = eid - timedelta(days=n)
        for period in pd.date_range(start, eid - timedelta(days=1), freq="D").to_period("M").unique():
            ms = period.to_timestamp()
            share = before_share(ms, [eid])
            row = {"event": name, "window_start": str(start), "window_end": str(eid - timedelta(days=1)),
                   "month": ms.strftime("%B %Y"), "share_of_window_in_month": round(share, 2)}
            for label, key in (("low", "lo_pct"), ("central", "uplift_pct"), ("high", "hi_pct")):
                pct = float(np.expm1(np.log1p(effect[key] / 100) * share) * 100)
                row[f"{label}_uplift_pct"] = round(pct, 1)
                row[f"{label}_extra_usd_m"] = round(monthly_level * pct / 100)
            rows.append(row)
    return pd.DataFrame(rows)


def run() -> None:
    config.PROCESSED.mkdir(parents=True, exist_ok=True)
    monthly, annual = load()
    fy = fiscal_years(monthly, annual)
    window = ten_month_window(monthly)
    summary = tiers(corridor_summary(fy, window))
    regions = region_shares(fy)

    total = monthly.groupby("month")["usd_million"].sum()
    d = detrend(total / total.index.days_in_month)
    effects = eid_effects(d["log_ratio"])
    pl = placebo(d["log_ratio"])
    real = effects["pooled"]["before_eid"]["uplift_pct"]
    seasonal = seasonal_index(d)
    by_corridor = corridor_seasonality(monthly)
    fy26_monthly = float(annual["fy26"].sum() / 12)
    calendar = planning_calendar(effects["pooled"]["before_eid"], fy26_monthly)

    totals_fy = fy.sum()
    gcc = summary[summary["region"] == "Gulf (GCC)"]
    top3 = summary.head(3)
    tier1 = summary[summary["tier"] == "Tier 1: core"]
    out = {
        "fy_totals_usd_m": {k: round(float(v), 1) for k, v in totals_fy.items()},
        "growth_fy21_pct": float((totals_fy["FY21"] / totals_fy["FY20"] - 1) * 100),
        "growth_fy23_pct": float((totals_fy["FY23"] / totals_fy["FY22"] - 1) * 100),
        "growth_fy26_pct": float((totals_fy["FY26"] / totals_fy["FY25"] - 1) * 100),
        "gcc_share_fy20_pct": float(gcc["share_fy20_pct"].sum()), "gcc_share_fy26_pct": float(gcc["share_fy26_pct"].sum()),
        "top3": top3["corridor"].tolist(), "top3_share_fy26_pct": float(top3["share_fy26_pct"].sum()),
        "hhi_fy20": hhi(fy["FY20"]), "hhi_fy23": hhi(fy["FY23"]), "hhi_fy26": hhi(fy["FY26"]),
        "n_corridors": len(config.CORRIDORS),
        "gcc_share_fy23_pct": float(regions.set_index("fiscal_year").loc["FY23", "Gulf (GCC)"]),
        "region_growth_fy26_pct": {r: float(v) for r, v in (fy[["FY25", "FY26"]].groupby(pd.Series(config.CORRIDOR_REGION)).sum()
                                   .pipe(lambda g: (g["FY26"] / g["FY25"] - 1) * 100)).items()},
        "tier1": tier1["corridor"].tolist(), "tier1_share_fy26_pct": float(tier1["share_fy26_pct"].sum()),
        "fast_risers": summary[summary["fast_riser"]]["corridor"].tolist(),
        "largest_adders": summary.sort_values("added_fy26_usd_m", ascending=False).head(3)[["corridor", "added_fy26_usd_m"]].values.tolist(),
        "months_used": [str(total.index.min().date()), str(total.index.max().date()), int(len(total))],
        "months_with_trend": int(d["ratio"].notna().sum()),
        "eid": effects,
        "placebo": {"n_shifts": int(len(pl)), "real_pct": real, "rank_of_real": int((pl["uplift_pct"] >= real).sum()) + 1,
                    "share_of_shifts_as_large": float((pl["uplift_pct"] >= real).mean())},
        "peak_calendar_month": int(seasonal.loc[seasonal["index"].idxmax(), "calendar_month"]),
        "peak_index_pct": float(seasonal["index_pct_vs_trend"].max()),
        "low_calendar_month": int(seasonal.loc[seasonal["index"].idxmin(), "calendar_month"]),
        "low_index_pct": float(seasonal["index_pct_vs_trend"].min()),
        "fy26_monthly_avg_usd_m": fy26_monthly,
        "jul_growth_pct": float((annual["jul_fy27p"].sum() / annual["jul_fy26"].sum() - 1) * 100),
        "events": config.EVENTS,
    }
    summary.round(4).to_csv(config.PROCESSED / "corridor_summary.csv", index=False, lineterminator="\n")
    fy.round(3).rename_axis("corridor").reset_index().to_csv(config.PROCESSED / "fiscal_years_by_corridor.csv", index=False, lineterminator="\n")
    regions.round(4).to_csv(config.PROCESSED / "region_share_by_fiscal_year.csv", index=False, lineterminator="\n")
    d.round(5).rename_axis("month").reset_index().to_csv(config.PROCESSED / "monthly_total_detrended.csv", index=False, lineterminator="\n")
    seasonal.round(5).to_csv(config.PROCESSED / "seasonal_index.csv", index=False, lineterminator="\n")
    by_corridor.round(5).to_csv(config.PROCESSED / "eid_effect_by_corridor.csv", index=False, lineterminator="\n")
    pl.round(4).to_csv(config.PROCESSED / "placebo_shifts.csv", index=False, lineterminator="\n")
    calendar.to_csv(config.PROCESSED / "planning_calendar.csv", index=False, lineterminator="\n")
    (config.PROCESSED / "summary.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    e = effects["pooled"]["before_eid"]
    print(f"[analyze] FY26 {totals_fy['FY26']:,.0f} m USD ({out['growth_fy26_pct']:+.1f}%); Gulf {out['gcc_share_fy26_pct']:.0f}%; "
          f"pre-Eid uplift {e['uplift_pct']:+.1f}% (95% {e['lo_pct']:+.1f} to {e['hi_pct']:+.1f}, p={e['p']:.2f}); "
          f"placebo rank {out['placebo']['rank_of_real']}/{len(pl) + 1}")
