"""Write README.md and the documents in docs/ from templates and the results, so a number in the text cannot drift
from the data. Edit the templates in remit/templates/docs, not the output.

A placeholder is {{name}} or {{name:format}} (a Python format such as .1f or ,.0f). A name with no value is an error.
"""

from __future__ import annotations

import json
import re

import pandas as pd

from . import config

TEMPLATE_DIR = config.TEMPLATES / "docs"
OUTPUTS = {"readme.md": config.ROOT / "README.md", "memo.md": config.DOCS / "recommendation_memo.md",
           "methodology.md": config.DOCS / "methodology.md", "data_sources.md": config.DOCS / "data_sources.md"}
PLACEHOLDER = re.compile(r"\{\{\s*(\w+)\s*(?::([^{}]+?))?\s*\}\}")


def render(template: str, values: dict) -> str:
    def fill(m: re.Match) -> str:
        name, fmt = m.group(1), m.group(2)
        if name not in values:
            raise KeyError(f"template uses {name!r}, which has no value")
        return format(values[name], fmt) if fmt else str(values[name])
    return PLACEHOLDER.sub(fill, template)


def _table(headers: list[str], rows: list[list], align: str) -> str:
    rule = ["---:" if a == "r" else "---" for a in align]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(rule) + " |"]
    lines += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(lines)


def _join(names: list[str]) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def context() -> dict:
    s = json.loads((config.PROCESSED / "summary.json").read_text(encoding="utf-8"))
    summary = pd.read_csv(config.PROCESSED / "corridor_summary.csv")
    by_corridor = pd.read_csv(config.PROCESSED / "eid_effect_by_corridor.csv").set_index("corridor")
    calendar = pd.read_csv(config.PROCESSED / "planning_calendar.csv")
    seasonal = pd.read_csv(config.PROCESSED / "seasonal_index.csv").set_index("calendar_month")
    regions = pd.read_csv(config.PROCESSED / "region_share_by_fiscal_year.csv")
    manifest = json.loads(config.MANIFEST.read_text(encoding="utf-8"))["files"]
    quality = json.loads((config.INTERIM / "data_quality.json").read_text(encoding="utf-8"))
    pooled, sep, pl = s["eid"]["pooled"], s["eid"]["separate"], s["placebo"]
    e = pooled["before_eid"]
    t = s["fy_totals_usd_m"]
    month = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    risers = summary[summary["fast_riser"]]
    tier2 = summary[summary["tier"] == "Tier 2: build"]
    adders = s["largest_adders"]
    gcc = summary[summary["region"] == "Gulf (GCC)"]
    uk, usa, oman = by_corridor.loc["UK"], by_corridor.loc["USA"], by_corridor.loc["Oman"]
    sa, uae = by_corridor.loc["Saudi Arabia"], by_corridor.loc["UAE"]
    clear = by_corridor[by_corridor["lo_pct"] > 0].sort_values("uplift_pct", ascending=False)
    top = summary.set_index("corridor")

    return {
        # totals
        "fy20_bn": t["FY20"] / 1000, "fy23_bn": t["FY23"] / 1000, "fy25_bn": t["FY25"] / 1000, "fy26_bn": t["FY26"] / 1000,
        "monthly_bn": s["fy26_monthly_avg_usd_m"] / 1000, "growth_fy26": s["growth_fy26_pct"], "growth_fy21": s["growth_fy21_pct"],
        "growth_fy23": s["growth_fy23_pct"], "jul_growth": s["jul_growth_pct"],
        # concentration
        "gcc26": s["gcc_share_fy26_pct"], "gcc20": s["gcc_share_fy20_pct"], "gcc23": s["gcc_share_fy23_pct"],
        "europe_growth": s["region_growth_fy26_pct"]["Europe"], "apac_growth": s["region_growth_fy26_pct"]["Asia-Pacific"],
        "namerica_growth": s["region_growth_fy26_pct"]["North America"], "top3": _join(s["top3"]), "top3_share": s["top3_share_fy26_pct"],
        "tier1": _join(s["tier1"]), "tier1_share": s["tier1_share_fy26_pct"], "n_corridors": s["n_corridors"],
        "hhi20": s["hhi_fy20"], "hhi26": s["hhi_fy26"],
        "saudi_share": top.loc["Saudi Arabia", "share_fy26_pct"], "uae_share": top.loc["UAE", "share_fy26_pct"],
        "uk_share": top.loc["UK", "share_fy26_pct"], "usa_share": top.loc["USA", "share_fy26_pct"],
        "uae_growth": top.loc["UAE", "growth_fy26_pct"], "saudi_growth": top.loc["Saudi Arabia", "growth_fy26_pct"],
        "uk_growth": top.loc["UK", "growth_fy26_pct"], "usa_growth": top.loc["USA", "growth_fy26_pct"],
        "oman_growth": top.loc["Oman", "growth_fy26_pct"], "australia_growth": top.loc["Australia", "growth_fy26_pct"],
        "risers": _join([f"{r.corridor} ({r.growth_fy26_pct:+.0f}%)" for r in risers.itertuples()]) if len(risers) else "none",
        "tier2": _join(tier2["corridor"].tolist()), "tier2_share": tier2["share_fy26_pct"].sum(),
        "adder1": adders[0][0], "adder1_m": adders[0][1], "adder2": adders[1][0], "adder2_m": adders[1][1],
        "adder3": adders[2][0], "adder3_m": adders[2][1], "added_total_m": summary["added_fy26_usd_m"].sum(),
        "gcc_growth": (gcc["fy26_usd_m"].sum() / gcc["fy25_usd_m"].sum() - 1) * 100,
        # seasonality
        "uplift": e["uplift_pct"], "uplift_lo": e["lo_pct"], "uplift_hi": e["hi_pct"], "uplift_p": e["p"],
        "fitr": sep["before_fitr"]["uplift_pct"], "fitr_p": sep["before_fitr"]["p"], "adha": sep["before_adha"]["uplift_pct"], "adha_p": sep["before_adha"]["p"],
        "after_eid": pooled["after_eid"]["uplift_pct"], "after_eid_p": pooled["after_eid"]["p"],
        "eid_r2": pooled["r2"], "one_over_n": 1 / s["n_corridors"], "placebo_n_minus_1": pl["n_shifts"], "n_major": config.N_MAJOR,
        "major_list": _join(by_corridor.index.tolist()), "n_trend": s["months_with_trend"], "n_months": s["months_used"][2],
        "first_month": pd.Timestamp(s["months_used"][0]).strftime("%B %Y"), "last_month": pd.Timestamp(s["months_used"][1]).strftime("%B %Y"),
        "placebo_share": pl["share_of_shifts_as_large"] * 100, "placebo_rank": pl["rank_of_real"], "placebo_n": pl["n_shifts"] + 1,
        "uk_eid": uk["uplift_pct"], "uk_eid_lo": uk["lo_pct"], "uk_eid_p": uk["p"], "usa_eid": usa["uplift_pct"], "usa_eid_p": usa["p"],
        "oman_eid": oman["uplift_pct"], "oman_eid_p": oman["p"], "saudi_eid": sa["uplift_pct"], "saudi_eid_p": sa["p"],
        "uae_eid": uae["uplift_pct"], "uae_eid_p": uae["p"], "clear_corridors": _join(clear.index.tolist()),
        "peak_month": month[s["peak_calendar_month"]], "peak_idx": s["peak_index_pct"], "low_month": month[s["low_calendar_month"]], "low_idx": s["low_index_pct"],
        "strong_months": _join([month[m] for m in seasonal[seasonal["index_pct_vs_trend"] >= 5].index]),
        "weak_months": _join([month[m] for m in seasonal[seasonal["index_pct_vs_trend"] <= -5].index]),
        "next_eids": _join(list(config.NEXT_EIDS)),
        "cal_central_max": calendar["central_extra_usd_m"].max(), "cal_high_max": calendar["high_extra_usd_m"].max(),
        # data
        "n_raw_files": len(manifest), "event_list": "; ".join(f"{k[:7]}: {v}" for k, v in config.EVENTS.items()),
        "window_days": config.EID_WINDOW_DAYS, "seed": config.SEED, "months_by_sbp": quality["workbook"]["months"][2],
        "first_workbook_month": pd.Timestamp(quality["workbook"]["months"][0]).strftime("%B %Y"),
        # tables
        "table_corridors": _table(["Corridor", "FY26 ($m)", "Share", "Growth on FY25", "Added ($m)", "Tier"],
                                  [[r.corridor, f"{r.fy26_usd_m:,.0f}", f"{r.share_fy26_pct:.1f}%", f"{r.growth_fy26_pct:+.1f}%",
                                    f"{r.added_fy26_usd_m:+,.0f}", r.tier] for r in summary.head(12).itertuples()], "lrrrrl"),
        "table_regions": _table(["Fiscal year"] + config.REGIONS, [[r["fiscal_year"]] + [f"{r[n]:.1f}%" for n in config.REGIONS] for _, r in regions.iterrows()], "l" + "r" * len(config.REGIONS)),
        "table_eid": _table(["Corridor", "Lift in the 21 days before Eid", "95% range", "p-value"],
                            [["**All corridors**", f"{e['uplift_pct']:+.1f}%", f"{e['lo_pct']:+.1f}% to {e['hi_pct']:+.1f}%", f"{e['p']:.2f}"]] +
                            [[c, f"{r.uplift_pct:+.1f}%", f"{r.lo_pct:+.1f}% to {r.hi_pct:+.1f}%", f"{r.p:.3f}"] for c, r in by_corridor.sort_values("uplift_pct", ascending=False).iterrows()], "lrrr"),
        "table_calendar": _table(["Event", "Three-week window", "Month", "Share of window", "Central", "Range", "Extra ($m, central)"],
                                 [[r.event, f"{r.window_start} to {r.window_end}", r.month, f"{r.share_of_window_in_month * 100:.0f}%",
                                   f"{r.central_uplift_pct:+.1f}%", f"{r.low_uplift_pct:+.1f}% to {r.high_uplift_pct:+.1f}%", f"{r.central_extra_usd_m:+,.0f}"]
                                  for r in calendar.itertuples()], "lllrrrr"),
        "table_files": _table(["File", "Bytes", "SHA-256 (first 12)", "Source"],
                              [[f"`data/raw/{k}`", f"{v['bytes']:,}", f"`{v['sha256'][:12]}`", v["source"].split("/")[2]] for k, v in manifest.items()], "lrll"),
    }


def render_all() -> dict:
    values = context()
    return {path: render((TEMPLATE_DIR / name).read_text(encoding="utf-8"), values) for name, path in OUTPUTS.items()}


def build() -> None:
    for path, text in render_all().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    print(f"[docs] wrote {len(OUTPUTS)} documents")
