"""The interactive dashboard: one HTML file with the data inside, Plotly from a CDN, and no server."""

from __future__ import annotations

import json

import pandas as pd
from plotly.offline import get_plotlyjs_version

from . import config

PAGE = config.TEMPLATES / "dashboard.html"


def payload() -> dict:
    summary = pd.read_csv(config.PROCESSED / "corridor_summary.csv")
    fy = pd.read_csv(config.PROCESSED / "fiscal_years_by_corridor.csv")
    regions = pd.read_csv(config.PROCESSED / "region_share_by_fiscal_year.csv")
    monthly = pd.read_csv(config.INTERIM / "monthly_by_corridor.csv", parse_dates=["month"])
    monthly = monthly[monthly["month"] >= config.FIRST_MONTH]
    wide = monthly.pivot(index="month", columns="corridor", values="usd_million")
    per_day = wide.div(wide.index.days_in_month, axis=0)
    detrended = pd.read_csv(config.PROCESSED / "monthly_total_detrended.csv")
    seasonal = pd.read_csv(config.PROCESSED / "seasonal_index.csv")
    by_corridor = pd.read_csv(config.PROCESSED / "eid_effect_by_corridor.csv")
    calendar = pd.read_csv(config.PROCESSED / "planning_calendar.csv")
    s = json.loads((config.PROCESSED / "summary.json").read_text(encoding="utf-8"))
    return {
        "summary": json.loads(summary.round(3).to_json(orient="records")),
        "fiscalYears": json.loads(fy.round(1).to_json(orient="records")),
        "regions": json.loads(regions.round(2).to_json(orient="records")),
        "regionNames": config.REGIONS,
        "months": [m.strftime("%Y-%m") for m in wide.index],
        "perDay": {c: [round(float(v), 3) for v in per_day[c]] for c in per_day.columns},
        "totalPerDay": [round(float(v), 3) for v in per_day.sum(axis=1)],
        "trend": [None if pd.isna(v) else round(float(v), 3) for v in detrended.set_index("month")["trend"].reindex(wide.index.strftime("%Y-%m-%d")).to_numpy()],
        "eidFitr": [d.isoformat() for d in config.EID_AL_FITR], "eidAdha": [d.isoformat() for d in config.EID_AL_ADHA],
        "events": [{"month": k, "text": v} for k, v in config.EVENTS.items()],
        "seasonal": json.loads(seasonal.round(3).to_json(orient="records")),
        "eidByCorridor": json.loads(by_corridor.round(2).to_json(orient="records")),
        "calendar": json.loads(calendar.to_json(orient="records")),
        "stats": s,
        "colours": {"Gulf (GCC)": config.NAVY, "Europe": config.TEAL, "North America": config.ORANGE, "Asia-Pacific": config.AMBER, "Other": config.GREY},
    }


def render() -> str:
    page = PAGE.read_text(encoding="utf-8")
    data = json.dumps(payload(), separators=(",", ":"), allow_nan=False)
    return (page.replace("__PLOTLY__", f"https://cdn.plot.ly/plotly-{get_plotlyjs_version()}.min.js")
            .replace("__DATA__", data.replace("</", "<\\/")))


def build() -> None:
    config.DASHBOARD.mkdir(parents=True, exist_ok=True)
    (config.DASHBOARD / "dashboard.html").write_text(render(), encoding="utf-8", newline="\n")
    (config.ROOT / "index.html").write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=dashboard/dashboard.html">'
        '<title>Pakistan remittance corridors</title><p><a href="dashboard/dashboard.html">Open the dashboard</a></p></html>\n',
        encoding="utf-8", newline="\n")
    print(f"[dashboard] {(config.DASHBOARD / 'dashboard.html').stat().st_size / 1e3:,.0f} kB")
