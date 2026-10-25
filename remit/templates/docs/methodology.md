# Methodology

This document explains how every number in the project is produced, what was checked, and what the methods cannot do. Numbers are filled in from the results, so they match the data. Code is in [`remit/`](../remit), and `python -m remit all` reproduces everything.

## 1. The question

A provider of remittance services to Pakistan needs to know **which corridors (sending countries) to serve first** and **when to expect the busiest weeks**. The first is a question about size, growth and concentration. The second is about seasonality, and in particular Eid, when families expect money.

## 2. Data

Two State Bank of Pakistan (SBP) files, both in million US dollars:

- **A monthly workbook by country**, {{first_workbook_month}} to {{last_month}} ({{months_by_sbp}} months, 30 country rows plus totals). SBP no longer publishes it at its own address, so the copy saved by the Internet Archive on 1 June 2024 is used.
- **The August 2026 Monthly Statistical Bulletin, table 4.8:** annual figures by country for FY25 and FY26, and for July of each.

Country figures use the remitter's original country from July 2019; before that they used the country of encashment. The analysis therefore starts in {{first_month}} ({{n_months}} months).

A **corridor** is a sending country, except that the UAE (Dubai, Abu Dhabi, Sharjah, others) is one corridor and five smaller EU countries are grouped as "Other EU". There are {{n_corridors}} corridors in five regions.

## 3. Checks made while building

Each check stops the build if it fails:

- Every country row SBP prints is present exactly once.
- The countries add up to the total in every month (largest gap under 0.001 million dollars).
- The UAE, other Gulf and EU groups add up to their members.
- For every fiscal year SBP prints a total beside the months; the months must add up to it (tested for the total, the USA, Saudi Arabia and Dubai).
- Months run without gaps and no value is blank or negative.
- In the bulletin, countries add up to the total for FY25 and FY26 to within a million dollars.

## 4. Size, growth and concentration

- **Fiscal years** run July to June. FY20 to FY23 come from the monthly workbook; FY25 and FY26 from the bulletin. FY24 cannot be built by country (the workbook ends in April 2024 and the bulletin starts at FY25), so the growth between FY20 and FY24 uses the same ten months, July to April, in each year.
- **Share** is a corridor's part of the year's total. **Growth** compares FY26 with FY25.
- **Concentration** is the Herfindahl index of corridor shares: {{hhi20:.3f}} in FY20 and {{hhi26:.3f}} in FY26 (it would be {{one_over_n:.3f}} if all {{n_corridors}} corridors were equal).
- **Tiers.** Tier 1 corridors have at least 8% of FY26 remittances, tier 2 from 1% to 8%, tier 3 under 1%. A *fast riser* is a single country outside tier 1, worth at least $500 million, whose growth beats the total by ten points or more. These cut-offs are a convenience, not a statistical result.

{{table_regions}}

## 5. Seasonality and the Eid effect

1. **Daily averages.** Each month's total is divided by its number of days, so February is not weak just for being short.
2. **Detrending.** Each daily average is divided by a centred 12-month moving average (the ratio-to-moving-average method). The trend absorbs the long-run level, including the jumps in 2020 and 2023, and any pattern that repeats every year. Six months are lost at each end, leaving {{n_trend}} of {{n_months}}.
3. **Eid windows.** For each month, the model counts what share of the {{window_days}} days before each Eid falls in that month (a month holding a whole window scores 1). Eid dates are those observed in Pakistan and can be a day out.
4. **Regression.** The log of the detrended ratio is regressed on the pooled pre-Eid share and on the share of the {{window_days}} days after Eid, with heteroskedasticity-robust (HC3) standard errors. The coefficient converts to a percentage lift. A second model separates Eid al-Fitr from Eid al-Adha.
5. **Placebo test.** All Eid dates are moved by the same number of days (from -150 to +150, skipping ±9 days around zero) and the model is refitted {{placebo_n_minus_1}} times. The real lift is {{uplift:+.1f}}%, and {{placebo_share:.0f}}% of shifted calendars give one at least as large.

**Result.** The pooled lift is {{uplift:+.1f}}% (95% range {{uplift_lo:+.1f}}% to {{uplift_hi:+.1f}}%, p = {{uplift_p:.2f}}, R² {{eid_r2:.2f}}). Separately, Eid al-Fitr gives {{fitr:+.1f}}% (p = {{fitr_p:.2f}}) and Eid al-Adha {{adha:+.1f}}% (p = {{adha_p:.2f}}). The share of days after Eid gives {{after_eid:+.1f}}% (p = {{after_eid_p:.2f}}), so there is no sign of a dip.

**By corridor** the same pooled model is run on the {{n_major}} largest single-country corridors over the period ({{major_list}}):

{{table_eid}}

{{n_major}} corridors were tested, so a single p-value below 0.05 is expected by chance about once in two sets of ten. The UK, USA and Oman stand out, and the USA and Oman would survive a Bonferroni correction for ten tests (p below 0.005); the UK is close.

## 6. Planning calendar

For the next two Eids the model's pooled estimate (central value and 95% range) is applied to each calendar month that the {{window_days}}-day window touches, in proportion to the share of the window in that month, to a monthly level equal to FY26's average of ${{monthly_bn:.1f}} billion. It is a planning range. It is not a forecast, and it uses approximate Eid dates ({{next_eids}}).

## 7. Reproducibility and testing

- Raw files, sources and SHA-256 checksums are in `data/raw/MANIFEST.json`; `python -m remit verify` fails if one changed.
- No random numbers are used in the analysis (the seed, {{seed}}, is recorded for completeness). No stage writes a timestamp.
- Package versions are pinned in `requirements.txt`.
- Tests cover the parsers and their checks, the seasonal model on data with a known Eid effect, the corridor tables, the dashboard and that the committed documents are what the templates and data produce.

## 8. What would change the conclusions

- **More months.** Data after April 2024 by country would add Eids and tighten the range. This is the single most useful improvement.
- **Another definition of the window.** Twenty-one days before Eid is a judgement; the result is similar for other lengths but not identical.
- **Informal channels.** If the share of money moving through formal channels changes (as it did in 2023), the series moves for reasons that have nothing to do with Eid. The trend absorbs most, not all, of this.
- **Country of remitter.** The series changed definition in July 2019, so earlier months are not used.
