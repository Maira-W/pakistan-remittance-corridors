# Pakistan remittance corridors: where the money comes from and when it arrives

[![tests](https://github.com/Maira-W/pakistan-remittance-corridors/actions/workflows/ci.yml/badge.svg)](https://github.com/Maira-W/pakistan-remittance-corridors/actions/workflows/ci.yml)
![python 3.11](https://img.shields.io/badge/python-3.11-blue)
[![licence: MIT](https://img.shields.io/badge/licence-MIT-green)](LICENSE)

Overseas Pakistanis sent home **${{fy26_bn:.1f}} billion** in the year to June 2026, about ${{monthly_bn:.1f}} billion a month. A bank, fintech or exchange house that wants a share of that money needs two answers: **which countries should it serve first, and when should it be ready for the busiest weeks?** This project answers both from the State Bank of Pakistan's own figures, and says how sure it is.

| | |
|---|---|
| **Interactive dashboard** | [maira-w.github.io/pakistan-remittance-corridors](https://maira-w.github.io/pakistan-remittance-corridors/) (five tabs: the big picture, corridors, when money arrives, where to focus, method) |
| **Recommendation memo** | [`docs/recommendation_memo.md`](docs/recommendation_memo.md) |
| **Method and data** | [methodology](docs/methodology.md) · [data sources](docs/data_sources.md) |
| **Data for Power BI or Excel** | [`data/processed`](data/processed) (plain CSV files) |

## What the data show

1. **The flow is large and growing.** FY26 brought ${{fy26_bn:.1f}} billion, {{growth_fy26:+.1f}}% on FY25 (${{fy25_bn:.1f}} billion). It was ${{fy20_bn:.1f}} billion in FY20.
2. **Four corridors carry {{tier1_share:.0f}}% of it:** {{tier1}}. The top three ({{top3}}) bring in {{top3_share:.0f}}%.
3. **The Gulf's lead has narrowed, early.** The Gulf states sent {{gcc20:.0f}}% in FY20 and {{gcc23:.0f}}% in FY23 as Europe and North America gained, and {{gcc26:.0f}}% in FY26: the share has been steady since FY23. In FY26 Europe ({{europe_growth:+.0f}}%) and Asia-Pacific ({{apac_growth:+.0f}}%) grew faster than the total ({{growth_fy26:+.1f}}%), the Gulf slightly slower ({{gcc_growth:+.1f}}%) and North America hardly at all ({{namerica_growth:+.1f}}%).
4. **Growth in FY26 came from a few places.** The largest gains in dollars were {{adder1}} (+${{adder1_m:,.0f}} million), {{adder2}} (+${{adder2_m:,.0f}} million) and {{adder3}} (+${{adder3_m:,.0f}} million). Among single countries outside the core, the fast risers were {{risers}}. The USA ({{usa_growth:+.1f}}%) and Oman ({{oman_growth:+.1f}}%) shrank.
5. **Money arrives in a wave before Eid, but the wave is modest and uncertain.** In the {{window_days}} days before Eid, remittances run about **{{uplift:+.1f}}%** above trend (95% range {{uplift_lo:+.1f}}% to {{uplift_hi:+.1f}}%). That is borderline: {{placebo_share:.0f}}% of made-up Eid calendars find a lift as large.
6. **The lift is clearest in the UK, USA and Oman.** The UK gains {{uk_eid:+.0f}}%, the USA {{usa_eid:+.0f}}% and Oman {{oman_eid:+.0f}}%, but the two largest corridors do not show a clear lift (Saudi Arabia {{saudi_eid:+.0f}}%, UAE {{uae_eid:+.0f}}%, neither distinguishable from zero).
7. **Some calendar months stand out.** In these years {{strong_months}} were the strongest months and {{weak_months}} the weakest (only three or four years behind each month, so read this as a pattern to check, not a rule).

<table>
<tr>
<td width="50%"><a href="docs/figures/01_corridor_shares.png"><img src="docs/figures/01_corridor_shares.png" alt="Share of remittances by corridor"></a><br><sub>Who sends the money, FY26</sub></td>
<td width="50%"><a href="docs/figures/02_region_mix.png"><img src="docs/figures/02_region_mix.png" alt="Share by region over time"></a><br><sub>The Gulf's share fell, then held</sub></td>
</tr>
<tr>
<td><a href="docs/figures/04_monthly_total.png"><img src="docs/figures/04_monthly_total.png" alt="Monthly remittances with Eid dates"></a><br><sub>Monthly remittances and the Eid dates</sub></td>
<td><a href="docs/figures/06_eid_by_corridor.png"><img src="docs/figures/06_eid_by_corridor.png" alt="Eid lift by corridor"></a><br><sub>The Eid lift differs by corridor</sub></td>
</tr>
</table>

All seven figures are in [`docs/figures`](docs/figures).

## What to do with it

- **Serve the core corridors first** ({{tier1}}), then the next tier ({{tier2}}).
- **Do not build on the Gulf alone.** It still sends {{gcc26:.0f}}%, but its share is down from {{gcc20:.0f}}% in FY20 and in FY26 Europe and Asia-Pacific grew faster.
- **Plan capacity and campaigns around Eid**, with the strongest case in the UK, USA and Oman. Treat the size of the lift as a range, not a number.
- **Check it against your own customers.** These are national totals, not one provider's flows.

The [memo](docs/recommendation_memo.md) gives the reasoning and the planning calendar for {{next_eids}}.

## How it works

```
data/raw  ──build──▶  data/interim  ──analyze──▶  data/processed  ──report──▶  docs/figures · dashboard/ · docs/
 (checksummed)         (clean, checked)            (results)                    (everything you open)
```

| Stage | What it does |
|---|---|
| `ingest` | Downloads the {{n_raw_files}} raw files once and records a SHA-256 checksum, source and date for each in [`data/raw/MANIFEST.json`](data/raw/MANIFEST.json). `verify` checks them. |
| `build` | Reads SBP's monthly workbook ({{first_workbook_month}} to {{last_month}}) and the bulletin's annual table; checks that countries add up to totals and months add up to SBP's own fiscal-year totals. |
| `analyze` | Corridor shares and growth, concentration, a ratio-to-trend seasonal model with Eid windows, a placebo test, tiers and a planning calendar. |
| `report` | Draws the figures, builds the dashboard and writes these documents. |

The documents (including this file) are written from [`remit/templates`](remit/templates) and the results, so a number in the text cannot disagree with the data. Edit the template, not the output.

## Data

| Source | Used for | Vintage |
|---|---|---|
| State Bank of Pakistan, country-wise workers' remittances workbook (Internet Archive copy) | Monthly remittances by country | {{first_workbook_month}} to {{last_month}} |
| State Bank of Pakistan, Monthly Statistical Bulletin, August 2026, table 4.8 | Annual remittances by country, FY25 and FY26 | to July 2026 |

SBP no longer publishes the workbook at its own address, which is why an archived copy is used. Details and every data problem found are in [`docs/data_sources.md`](docs/data_sources.md).

## Quality checks

- **Everything adds up.** Countries sum to the total, groups sum to their members, and every month sums to SBP's printed fiscal-year totals, or the build stops.
- **Raw files cannot change silently.** Each has a checksum, checked in CI.
- **A placebo test** moves the Eid dates by 9 to 150 days and refits, to show how unusual the real result is.
- **Tests** cover the parsers, the model on a case with a known answer, the documents and the dashboard. They run on every push.

## Limitations

- Monthly country data end in {{last_month}}, so the Eid result rests on {{n_trend}} months and about nine Eids. FY24 is missing at country level.
- These are remittances through formal channels recorded by the central bank. Informal flows are not counted.
- US dollars only; exchange-rate effects are not modelled.
- The Eid result is borderline for the total, and the corridor results are exploratory ({{n_major}} were tested).
- Associations, not causes: {{event_list}}.

## Reproduce it

```bash
python -m venv .venv && .venv\Scripts\activate        # macOS or Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
python -m remit verify          # raw files match their checksums
python -m remit all             # build, analyze and report (under a minute)
pytest                          # run the tests
```

Outputs are deterministic (seed {{seed}}). `python -m remit ingest --refresh` downloads the raw files again, which needs the internet and a patient wait for the State Bank's server.

## Layout

```
remit/             the package: ingest, build, analysis, charts, dashboard, docs
  templates/       dashboard page and document templates
data/raw/          source files and MANIFEST.json (checksums)
data/interim/      cleaned tables
data/processed/    results as CSV and JSON
docs/              memo, methodology, data sources, figures
dashboard/         the interactive dashboard (one HTML file)
tests/             pytest suite
.github/workflows/ continuous integration
```

## Licence

The code and documents are released under the [MIT licence](LICENSE). The data are State Bank of Pakistan statistics; see [`docs/data_sources.md`](docs/data_sources.md).
