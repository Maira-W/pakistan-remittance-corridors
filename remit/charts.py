"""Seven static figures for the README and the memo (docs/figures)."""

from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from . import config  # noqa: E402

REGION_COLOUR = {"Gulf (GCC)": config.NAVY, "Europe": config.TEAL, "North America": config.ORANGE,
                 "Asia-Pacific": config.AMBER, "Other": config.GREY}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

plt.rcParams.update({"figure.dpi": 150, "savefig.dpi": 160, "font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.edgecolor": "#9AA5B1", "axes.titleweight": "bold",
                     "axes.titlesize": 12.5, "axes.titlelocation": "left", "font.family": "DejaVu Sans"})


def _save(fig, name: str, note: str | None = None) -> None:
    config.FIGURES.mkdir(parents=True, exist_ok=True)
    if note:
        fig.text(0.01, 0.005, note, fontsize=7.5, color="#5B6575", ha="left", va="bottom")
    fig.savefig(config.FIGURES / name, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _title(ax, title: str, sub: str) -> None:
    ax.set_title(title, pad=22)
    ax.text(0, 1.02, sub, transform=ax.transAxes, fontsize=9, color="#5B6575", va="bottom")


def fig_shares(summary: pd.DataFrame) -> None:
    s = summary.sort_values("fy26_usd_m")
    fig, ax = plt.subplots(figsize=(7.2, 6.6))
    ax.barh(s["corridor"], s["share_fy26_pct"], color=[REGION_COLOUR[r] for r in s["region"]])
    for y, (v, g) in enumerate(zip(s["share_fy26_pct"], s["growth_fy26_pct"])):
        ax.text(v + 0.3, y, f"{v:.1f}%  ({g:+.0f}% on FY25)", va="center", fontsize=8)
    ax.set_xlim(0, s["share_fy26_pct"].max() * 1.45)
    ax.set_xlabel("Share of FY26 remittances (%)")
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in REGION_COLOUR.values()]
    ax.legend(handles, REGION_COLOUR, loc="lower right", frameon=False, fontsize=8.5)
    _title(ax, "Four corridors bring in 69% of the money", f"FY26 (July 2025 to June 2026), total {s['fy26_usd_m'].sum():,.0f} million US dollars")
    _save(fig, "01_corridor_shares.png", "Source: State Bank of Pakistan, Monthly Statistical Bulletin, August 2026, table 4.8.")


def fig_regions(regions: pd.DataFrame) -> None:
    r = regions.set_index("fiscal_year")
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    left = np.zeros(len(r))
    for region in config.REGIONS:
        ax.bar(r.index, r[region], bottom=left, color=REGION_COLOUR[region], label=region, width=0.65)
        for i, v in enumerate(r[region]):
            if v > 5:
                ax.text(i, left[i] + v / 2, f"{v:.0f}%", ha="center", va="center", color="white", fontsize=8, fontweight="bold")
        left += r[region].to_numpy()
    ax.set_ylabel("Share of remittances (%)")
    ax.set_ylim(0, 100)
    ax.legend(ncol=5, frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.1))
    _title(ax, "The Gulf's share fell from 65% to 53% by FY23, then held", "Fiscal years; FY24 is missing at country level (the workbook ends in April 2024)")
    _save(fig, "02_region_mix.png", "Sources: SBP country-wise workers' remittances workbook; SBP Monthly Statistical Bulletin, August 2026.")


def fig_growth(summary: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 5))
    for _, r in summary.iterrows():
        ax.scatter(r["fy26_usd_m"], r["growth_fy26_pct"], s=60, color=REGION_COLOUR[r["region"]], alpha=0.9, edgecolor="white", linewidth=0.6)
    total = (summary["fy26_usd_m"].sum() / summary["fy25_usd_m"].sum() - 1) * 100
    ax.axhline(total, color="#333", lw=1, ls="--")
    ax.text(summary["fy26_usd_m"].min(), total + 1.2, f"all corridors: {total:+.1f}%", fontsize=8.5)
    ax.axhline(0, color="#9AA5B1", lw=0.8)
    label = set(summary[summary["tier"] == "Tier 1: core"]["corridor"]) | set(summary[summary["fast_riser"]]["corridor"]) | {"Italy", "Oman"}
    for _, r in summary[summary["corridor"].isin(label)].iterrows():
        ax.annotate(r["corridor"], (r["fy26_usd_m"], r["growth_fy26_pct"]), xytext=(5, 4), textcoords="offset points", fontsize=8.5)
    ax.set_xscale("log")
    ax.set_xlabel("FY26 remittances (million US dollars, log scale)")
    ax.set_ylabel("Growth on FY25 (%)")
    _title(ax, "Bigger corridors are not the fastest growing", "Each dot is a corridor; FY26 against FY25")
    _save(fig, "03_growth_vs_size.png", "Source: SBP Monthly Statistical Bulletin, August 2026, table 4.8.")


def fig_monthly(detrended: pd.DataFrame) -> None:
    d = detrended.copy()
    d["month"] = pd.to_datetime(d["month"])
    fig, ax = plt.subplots(figsize=(8, 4.4))
    ax.plot(d["month"], d["usd_m_per_day"], color=config.NAVY, lw=1.8, label="Daily average of the month")
    ax.plot(d["month"], d["trend"], color=config.ORANGE, lw=1.6, ls="--", label="12-month trend")
    for eids, name in ((config.EID_AL_FITR, "Eid al-Fitr"), (config.EID_AL_ADHA, "Eid al-Adha")):
        for i, e in enumerate(eids):
            ax.axvline(pd.Timestamp(e), color=config.TEAL if "Fitr" in name else config.PURPLE, alpha=0.55, lw=1.1, label=name if i == 0 else None)
    for start, text in config.EVENTS.items():
        ax.annotate(text, (pd.Timestamp(start), d["usd_m_per_day"].max() * 1.02), fontsize=7, rotation=90, va="top", ha="right", color="#5B6575")
    ax.set_ylabel("Million US dollars a day")
    ax.legend(frameon=False, fontsize=8, ncol=2, loc="lower right")
    _title(ax, "Remittances ride a rising trend with bumps around Eid", "Monthly workers' remittances, July 2019 to April 2024, per day")
    _save(fig, "04_monthly_total.png", "Source: SBP country-wise workers' remittances workbook. Eid dates are those observed in Pakistan, give or take a day.")


def fig_seasonal(seasonal: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4))
    colour = [config.TEAL if v >= 0 else config.GREY for v in seasonal["index_pct_vs_trend"]]
    ax.bar([MONTHS[m - 1] for m in seasonal["calendar_month"]], seasonal["index_pct_vs_trend"], color=colour)
    ax.errorbar([MONTHS[m - 1] for m in seasonal["calendar_month"]], seasonal["index_pct_vs_trend"], yerr=seasonal["sd"] * 100 / np.sqrt(seasonal["years"]),
                fmt="none", ecolor="#333", capsize=2, lw=0.9)
    ax.axhline(0, color="#333", lw=0.8)
    ax.set_ylabel("Against the 12-month trend (%)")
    _title(ax, "January is the weakest month, March, April and June the strongest",
           "Average daily remittances by calendar month, relative to trend (bars: one standard error)")
    _save(fig, "05_seasonal_index.png", "Only three or four years per month (46 months in all), and Eid moves about 11 days earlier each year.")


def fig_eid(by_corridor: pd.DataFrame, total: dict) -> None:
    rows = [("All corridors", total["uplift_pct"], total["lo_pct"], total["hi_pct"])] + \
           [(r.corridor, r.uplift_pct, r.lo_pct, r.hi_pct) for r in by_corridor.sort_values("uplift_pct").itertuples()]
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    for i, (name, v, lo, hi) in enumerate(rows):
        colour = config.NAVY if name == "All corridors" else (config.TEAL if lo > 0 else config.GREY)
        ax.plot([lo, hi], [i, i], color=colour, lw=2)
        ax.scatter(v, i, color=colour, zorder=3, s=36)
    ax.set_yticks(range(len(rows)), [r[0] for r in rows])
    ax.axvline(0, color="#333", lw=0.9)
    ax.set_xlabel("Extra remittances in the 21 days before Eid, against trend (%, with 95% range)")
    _title(ax, "The Eid lift is clear for the UK, USA and Oman, not for the big Gulf corridors",
           "Teal: the range stays above zero. Ten corridors tested, so treat single results with care.")
    _save(fig, "06_eid_by_corridor.png", "46 months, July 2019 to April 2024. Robust (HC3) standard errors.")


def fig_placebo(placebo: pd.DataFrame, real: float) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    ax.hist(placebo["uplift_pct"], bins=22, color=config.GREY, edgecolor="white")
    ax.axvline(real, color=config.ORANGE, lw=2)
    share = (placebo["uplift_pct"] >= real).mean() * 100
    ax.text(real, ax.get_ylim()[1] * 0.92, f"  real Eid dates: {real:+.1f}%", color=config.ORANGE, fontsize=9, fontweight="bold")
    ax.set_xlabel("Estimated pre-Eid lift when every Eid is moved by the same number of days (%)")
    ax.set_ylabel("Number of shifted calendars")
    _title(ax, f"{share:.0f}% of made-up calendars find a lift this large", "Placebo test: the same model on Eid dates shifted by 9 to 150 days either way")
    _save(fig, "07_placebo_test.png", "A lift that real Eid dates find far more often than shifted ones would be convincing; this one is suggestive, not proven.")


def make_all() -> None:
    summary = pd.read_csv(config.PROCESSED / "corridor_summary.csv")
    regions = pd.read_csv(config.PROCESSED / "region_share_by_fiscal_year.csv")
    detrended = pd.read_csv(config.PROCESSED / "monthly_total_detrended.csv")
    seasonal = pd.read_csv(config.PROCESSED / "seasonal_index.csv")
    by_corridor = pd.read_csv(config.PROCESSED / "eid_effect_by_corridor.csv")
    placebo = pd.read_csv(config.PROCESSED / "placebo_shifts.csv")
    s = json.loads((config.PROCESSED / "summary.json").read_text(encoding="utf-8"))
    fig_shares(summary)
    fig_regions(regions)
    fig_growth(summary)
    fig_monthly(detrended)
    fig_seasonal(seasonal)
    fig_eid(by_corridor, s["eid"]["pooled"]["before_eid"])
    fig_placebo(placebo, s["placebo"]["real_pct"])
