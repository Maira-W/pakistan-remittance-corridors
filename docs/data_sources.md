# Data sources

Everything in this project comes from two public State Bank of Pakistan (SBP) publications. The raw files are stored in [`data/raw`](../data/raw) with a manifest ([`MANIFEST.json`](../data/raw/MANIFEST.json)) that records each file's source, date, size and SHA-256 checksum; `python -m remit verify` checks that nothing has changed.

## Sources

| Source | What it gives | Vintage | How it is used |
|---|---|---|---|
| **SBP, country-wise workers' remittances workbook** (`Homeremit_Arch.xlsx`), as saved by the Internet Archive on 1 June 2024 | Monthly remittances by country in million US dollars, with SBP's own fiscal-year totals | July 2018 to April 2024 (the analysis uses July 2019 on) | Monthly series, seasonality, FY20 to FY23 |
| **SBP, Monthly Statistical Bulletin, August 2026**, table 4.8 (page 107) | Annual remittances by country for FY25 and FY26, and July of each (provisional for July 2026) | FY25, FY26 | Latest shares and growth |

## Terms of use

SBP statistics are public data published by the State Bank of Pakistan; cite the source. The code in this repository is the author's own work, released under the MIT licence ([`LICENSE`](../LICENSE)); the data keep the terms above. This project is independent and is not endorsed by the State Bank of Pakistan.

## Raw files

| File | Bytes | SHA-256 (first 12) | Source |
| --- | ---: | --- | --- |
| `data/raw/sbp/Homeremit_Arch_2024-06-01.xlsx` | 191,371 | `909775b3bae8` | web.archive.org |
| `data/raw/sbp/MSB_Aug2026_table_4_8_workers_remittances.pdf` | 195,665 | `041f061e7268` | www.sbp.org.pk |

## Data problems found, and what was done

1. **SBP stopped publishing the workbook at its own address.** Its old links (for example `ecodata/Homeremit.pdf` and `ecodata/Homeremit_Arch.xlsx`) now return the website's front page with a success code, so a download "works" but is not data. The build therefore uses the Internet Archive's copy and the manifest records its address. The ingest step refuses a file that does not start like the expected file type.
2. **The workbook mixes date formats.** Early columns are dates with odd days (the 17th, 10th, 31st), later ones are text such as `Jan-24` or `Mar-24R` (the R marks a revision), and fiscal-year totals sit between the months. The parser reads all of them and uses the fiscal-year totals as a check.
3. **A series break in July 2019.** From July 2019 SBP records the remitter's original country; before that, the country of encashment. Country analysis starts in July 2019.
4. **Roshan Digital Account transfers are counted from September 2020.** The monthly series jumps that month for that reason as well as the pandemic recovery; the 12-month trend absorbs the jump, but it is not seasonal.
5. **FY24 is missing at country level.** The workbook ends in April 2024 and the bulletin shows FY25 and FY26 only. Growth over the earlier years uses the same ten months (July to April).
6. **A monthly table in the bulletin is ambiguous.** The bulletin's "selected indicators" pages list monthly totals, but the July column of the 2026 page repeats July 2025's figure under a 2026 heading. These monthly totals are not used; only table 4.8 is.
7. **A late-2024 SBP PDF has garbled digits.** Text extraction from an archived October 2024 country-wise PDF splits numbers with spaces ("4 29.5"). It is not used, so country-level months stop at April 2024.
8. **Groups of small countries.** SBP's "Other countries" includes encashments from foreign-currency instruments and some EU countries not listed separately. It, and the five smaller EU countries grouped here as "Other EU", are not counted as corridors a provider could serve.
9. **Figures are provisional and revised.** The latest month in each source is provisional, and at least one month in the workbook (March 2024) is marked revised.
