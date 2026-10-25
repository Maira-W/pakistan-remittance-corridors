# Methodology

This document explains how every number in the project is produced, what was checked, and what the methods cannot do. Numbers are filled in from the results, so they match the data. Code is in [`remit/`](../remit), and `python -m remit all` reproduces everything.

## 1. The question

A provider of remittance services to Pakistan needs to know **which corridors (sending countries) to serve first** and **when to expect the busiest weeks**. The first is a question about size, growth and concentration. The second is about seasonality, and in particular Eid, when families expect money.

## 2. Data

Two State Bank of Pakistan (SBP) files, both in million US dollars:

- **A monthly workbook by country**, July 2018 to April 2024 (70 months, 30 country rows plus totals). SBP no longer publishes it at its own address, so the copy saved by the Internet Archive on 1 June 2024 is used.
- **The August 2026 Monthly Statistical Bulletin, table 4.8:** annual figures by country for FY25 and FY26, and for July of each.

Country figures use the remitter's original country from July 2019; before that they used the country of encashment. The analysis therefore starts in July 2019 (58 months).

A **corridor** is a sending country, except that the UAE (Dubai, Abu Dhabi, Sharjah, others) is one corridor and five smaller EU countries are grouped as "Other EU". There are 23 corridors in five regions.

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
- **Concentration** is the Herfindahl index of corridor shares: 0.165 in FY20 and 0.138 in FY26 (it would be 0.043 if all 23 corridors were equal).
- **Tiers.** Tier 1 corridors have at least 8% of FY26 remittances, tier 2 from 1% to 8%, tier 3 under 1%. A *fast riser* is a single country outside tier 1, worth at least $500 million, whose growth beats the total by ten points or more. These cut-offs are a convenience, not a statistical result.

| Fiscal year | Gulf (GCC) | Europe | North America | Asia-Pacific | Other |
| --- | ---: | ---: | ---: | ---: | ---: |
| FY20 | 65.4% | 19.2% | 8.9% | 2.9% | 3.5% |
| FY21 | 58.5% | 23.7% | 10.8% | 3.3% | 3.7% |
| FY22 | 55.1% | 25.7% | 12.1% | 3.4% | 3.6% |
| FY23 | 52.6% | 26.9% | 13.6% | 3.2% | 3.6% |
| FY25 | 54.5% | 27.7% | 11.4% | 3.1% | 3.2% |
| FY26 | 54.2% | 28.3% | 10.6% | 3.6% | 3.3% |

## 5. Seasonality and the Eid effect

1. **Daily averages.** Each month's total is divided by its number of days, so February is not weak just for being short.
2. **Detrending.** Each daily average is divided by a centred 12-month moving average (the ratio-to-moving-average method). The trend absorbs the long-run level, including the jumps in 2020 and 2023, and any pattern that repeats every year. Six months are lost at each end, leaving 46 of 58.
3. **Eid windows.** For each month, the model counts what share of the 21 days before each Eid falls in that month (a month holding a whole window scores 1). Eid dates are those observed in Pakistan and can be a day out.
4. **Regression.** The log of the detrended ratio is regressed on the pooled pre-Eid share and on the share of the 21 days after Eid, with heteroskedasticity-robust (HC3) standard errors. The coefficient converts to a percentage lift. A second model separates Eid al-Fitr from Eid al-Adha.
5. **Placebo test.** All Eid dates are moved by the same number of days (from -150 to +150, skipping ±9 days around zero) and the model is refitted 96 times. The real lift is +10.6%, and 12% of shifted calendars give one at least as large.

**Result.** The pooled lift is +10.6% (95% range -1.3% to +23.9%, p = 0.08, R² 0.14). Separately, Eid al-Fitr gives +6.4% (p = 0.55) and Eid al-Adha +14.7% (p = 0.05). The share of days after Eid gives -4.1% (p = 0.29), so there is no sign of a dip.

**By corridor** the same pooled model is run on the 10 largest single-country corridors over the period (Saudi Arabia, UAE, UK, USA, Oman, Qatar, Kuwait, Italy, Australia and Canada):

| Corridor | Lift in the 21 days before Eid | 95% range | p-value |
| --- | ---: | ---: | ---: |
| **All corridors** | +10.6% | -1.3% to +23.9% | 0.08 |
| Canada | +25.2% | +12.7% to +39.2% | 0.000 |
| UK | +22.8% | +5.1% to +43.6% | 0.010 |
| USA | +20.4% | +6.6% to +35.9% | 0.003 |
| Oman | +15.8% | +9.3% to +22.8% | 0.000 |
| UAE | +8.5% | -4.6% to +23.4% | 0.213 |
| Australia | +8.5% | -4.2% to +22.8% | 0.198 |
| Saudi Arabia | +7.0% | -5.0% to +20.6% | 0.266 |
| Qatar | +5.3% | -7.1% to +19.3% | 0.420 |
| Italy | +4.6% | -11.0% to +23.0% | 0.582 |
| Kuwait | -7.2% | -34.2% to +30.9% | 0.671 |

10 corridors were tested, so a single p-value below 0.05 is expected by chance about once in two sets of ten. The UK, USA and Oman stand out, and the USA and Oman would survive a Bonferroni correction for ten tests (p below 0.005); the UK is close.

## 6. Planning calendar

For the next two Eids the model's pooled estimate (central value and 95% range) is applied to each calendar month that the 21-day window touches, in proportion to the share of the window in that month, to a monthly level equal to FY26's average of $3.5 billion. It is a planning range. It is not a forecast, and it uses approximate Eid dates (Eid al-Fitr 2027 and Eid al-Adha 2027).

## 7. Reproducibility and testing

- Raw files, sources and SHA-256 checksums are in `data/raw/MANIFEST.json`; `python -m remit verify` fails if one changed.
- No random numbers are used in the analysis (the seed, 42, is recorded for completeness). No stage writes a timestamp.
- Package versions are pinned in `requirements.txt`.
- Tests cover the parsers and their checks, the seasonal model on data with a known Eid effect, the corridor tables, the dashboard and that the committed documents are what the templates and data produce.

## 8. What would change the conclusions

- **More months.** Data after April 2024 by country would add Eids and tighten the range. This is the single most useful improvement.
- **Another definition of the window.** Twenty-one days before Eid is a judgement; the result is similar for other lengths but not identical.
- **Informal channels.** If the share of money moving through formal channels changes (as it did in 2023), the series moves for reasons that have nothing to do with Eid. The trend absorbs most, not all, of this.
- **Country of remitter.** The series changed definition in July 2019, so earlier months are not used.
