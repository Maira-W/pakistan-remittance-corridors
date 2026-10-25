"""Constants shared by every stage: where the data come from, how countries are grouped, and the Eid calendar."""

from __future__ import annotations

from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"
DOCS = ROOT / "docs"
FIGURES = DOCS / "figures"
DASHBOARD = ROOT / "dashboard"
TEMPLATES = Path(__file__).resolve().parent / "templates"
MANIFEST = RAW / "MANIFEST.json"

SEED = 42

# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------
# SBP's country-wise workers' remittances workbook. SBP has stopped publishing it at its own address (the old links now
# return the website's front page), so the copy kept by the Internet Archive on 2024-06-01 is the source.
ARCHIVE_URL = "http://web.archive.org/web/20240601163239id_/https://www.sbp.org.pk/Ecodata/Homeremit_Arch.xlsx"
ARCHIVE_FILE = "sbp/Homeremit_Arch_2024-06-01.xlsx"
ARCHIVE_SHEET = "July 2018 onwards "  # SBP's sheet name ends with a space

# SBP Monthly Statistical Bulletin, August 2026, table 4.8 (PDF page 107): annual figures by country for FY25 and FY26.
BULLETIN_URL = "https://www.sbp.org.pk/assets/document/publications/MSB-Complete-August-2026.pdf"
BULLETIN_PAGE = 107
BULLETIN_FILE = "sbp/MSB_Aug2026_table_4_8_workers_remittances.pdf"

# Remittances are recorded by the remitter's original country from July 2019; before that, by the country of encashment.
FIRST_MONTH = "2019-07-01"

# ---------------------------------------------------------------------------
# Countries
# ---------------------------------------------------------------------------
# SBP's rows, in order, with the corridor each one belongs to. A corridor is a country, except that the UAE is one
# corridor (Dubai, Abu Dhabi, Sharjah and others together) and the smaller EU countries are grouped.
LEAF_TO_CORRIDOR = {
    "USA": "USA", "U.K.": "UK", "Saudi Arabia": "Saudi Arabia",
    "Dubai": "UAE", "Abu Dhabi": "UAE", "Sharjah": "UAE", "Others": "UAE",
    "Bahrain": "Bahrain", "Kuwait": "Kuwait", "Qatar": "Qatar", "Oman": "Oman",
    "Germany": "Germany", "France": "France", "Spain": "Spain", "Italy": "Italy", "Greece": "Greece",
    "Netherland": "Other EU", "Sweden": "Other EU", "Denmark": "Other EU", "Ireland": "Other EU", "Belgium": "Other EU",
    "Malaysia*": "Malaysia", "Norway": "Norway", "Switzerland": "Switzerland", "Australia": "Australia",
    "Canada": "Canada", "Japan": "Japan", "South Africa*": "South Africa", "South Korea*": "South Korea",
    "Other Countries#": "Other countries",
}
CORRIDOR_REGION = {
    "Saudi Arabia": "Gulf (GCC)", "UAE": "Gulf (GCC)", "Bahrain": "Gulf (GCC)", "Kuwait": "Gulf (GCC)",
    "Qatar": "Gulf (GCC)", "Oman": "Gulf (GCC)",
    "UK": "Europe", "Germany": "Europe", "France": "Europe", "Spain": "Europe", "Italy": "Europe", "Greece": "Europe",
    "Other EU": "Europe", "Norway": "Europe", "Switzerland": "Europe",
    "USA": "North America", "Canada": "North America",
    "Malaysia": "Asia-Pacific", "Australia": "Asia-Pacific", "Japan": "Asia-Pacific", "South Korea": "Asia-Pacific",
    "South Africa": "Other", "Other countries": "Other",
}
CORRIDORS = list(dict.fromkeys(LEAF_TO_CORRIDOR.values()))
REGIONS = list(dict.fromkeys(CORRIDOR_REGION.values()))

# Groups of small countries rather than places a provider could serve
AGGREGATES = ["Other EU", "Other countries"]

# The corridors big enough for a month-by-month analysis of their own are the largest single countries over the period
# (the others are too small and noisy).
N_MAJOR = 10

# ---------------------------------------------------------------------------
# Eid calendar (Pakistan, first day of Eid; the date can move by a day with the moon sighting)
# ---------------------------------------------------------------------------
EID_AL_FITR = [date(2019, 6, 5), date(2020, 5, 25), date(2021, 5, 14), date(2022, 5, 3), date(2023, 4, 22), date(2024, 4, 11)]
EID_AL_ADHA = [date(2019, 8, 12), date(2020, 8, 1), date(2021, 7, 21), date(2022, 7, 10), date(2023, 6, 29), date(2024, 6, 17)]
# Planning dates for the next two Eids after the data (approximate)
NEXT_EIDS = {"Eid al-Fitr 2027": date(2027, 3, 10), "Eid al-Adha 2027": date(2027, 5, 17)}
EID_WINDOW_DAYS = 21  # remittances are sent in the weeks before Eid

# Events that moved remittances for reasons other than the calendar
EVENTS = {
    "2020-03-01": "COVID-19 lockdowns",
    "2020-09-01": "Roshan Digital Account transfers counted",
    "2023-07-01": "Exchange-rate reforms and a crackdown on informal channels",
}

# Palette shared by the figures and the dashboard
NAVY, TEAL, ORANGE, AMBER, GREY, PURPLE = "#1F3B57", "#2A9D8F", "#E76F51", "#E9C46A", "#9AA5B1", "#7B4FA3"
