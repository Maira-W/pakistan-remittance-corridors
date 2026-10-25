# Memo: which corridors to serve first, and when to be ready

**For:** the product and treasury teams of a bank, exchange house or fintech that wants a share of remittances to Pakistan
**Evidence:** this repository. State Bank of Pakistan figures: annual by country to FY26, monthly by country from {{first_month}} to {{last_month}}.

## Bottom line

Serve **{{tier1}}** first: together they bring in {{tier1_share:.0f}}% of the ${{fy26_bn:.1f}} billion Pakistan received in FY26. Add the next tier as you grow, and watch the fast risers ({{risers}}). Be ready for the {{window_days}} days before each Eid, when remittances run about {{uplift:+.0f}}% above trend, and expect the UK, USA and Oman to show the clearest lift. The size of that lift is uncertain, so plan for a range.

## What the data show

**The flow is large and still growing.** ${{fy26_bn:.1f}} billion in FY26 is {{growth_fy26:+.1f}}% on FY25. The dip after FY22 (${{fy23_bn:.1f}} billion in FY23) has been more than recovered. July 2026 was {{jul_growth:+.0f}}% on July 2025.

**It is concentrated, but less than it was.** The Gulf states sent {{gcc20:.0f}}% of the money in FY20, {{gcc23:.0f}}% in FY23 and {{gcc26:.0f}}% in FY26: most of the fall came early, and the share has been steady since. Saudi Arabia ({{saudi_share:.0f}}%), the UAE ({{uae_share:.0f}}%), the UK ({{uk_share:.0f}}%) and the USA ({{usa_share:.0f}}%) are the four large corridors. A standard concentration index across the {{n_corridors}} corridors fell from {{hhi20:.2f}} to {{hhi26:.2f}}.

**Growth is not where the size is.** The FY26 gain of ${{added_total_m:,.0f}} million came mostly from {{adder1}} (+${{adder1_m:,.0f}} million), {{adder2}} (+${{adder2_m:,.0f}} million) and {{adder3}} (+${{adder3_m:,.0f}} million). Outside the core, {{risers}} grew fastest. The USA ({{usa_growth:+.1f}}%) and Oman ({{oman_growth:+.1f}}%) shrank, and Saudi Arabia grew only {{saudi_growth:+.1f}}%.

**Money surges before Eid, modestly.** After removing the long-run trend, remittances run about {{uplift:+.1f}}% above normal in the {{window_days}} days before Eid (95% range {{uplift_lo:+.1f}}% to {{uplift_hi:+.1f}}%, p = {{uplift_p:.2f}}). Eid al-Adha shows a clearer lift ({{adha:+.0f}}%, p = {{adha_p:.2f}}) than Eid al-Fitr ({{fitr:+.0f}}%, p = {{fitr_p:.2f}}). There is no sign of a dip afterwards ({{after_eid:+.1f}}%, p = {{after_eid_p:.2f}}).

**The evidence is suggestive, not conclusive.** If the Eid dates are moved by the same number of days, {{placebo_share:.0f}}% of the made-up calendars find a lift as large ({{placebo_rank}}th largest of {{placebo_n}}). With {{n_trend}} usable months and only about nine Eids, the total cannot prove the effect.

**The lift is clearest for the diaspora corridors.** The UK ({{uk_eid:+.0f}}%, p = {{uk_eid_p:.3f}}), the USA ({{usa_eid:+.0f}}%, p = {{usa_eid_p:.3f}}) and Oman ({{oman_eid:+.0f}}%, p = {{oman_eid_p:.3f}}) show a clear lift. Saudi Arabia ({{saudi_eid:+.0f}}%) and the UAE ({{uae_eid:+.0f}}%) do not. {{n_major}} corridors were tested, so single results should be read with care.

**Some calendar months stand out.** {{strong_months}} were strong months and {{weak_months}} weak ones, measured per day so that short months do not look weak. Only three or four years sit behind each month. The strongest month averages {{peak_idx:+.0f}}% against trend and the weakest {{low_idx:+.0f}}%.

## Recommendations

**1. Build for the four core corridors first.** {{tier1}} carry {{tier1_share:.0f}}% of the money. Price, speed and the receiving side (wallets, bank accounts, cash pick-up) matter most here, because small improvements apply to a large flow.

**2. Add the next tier and watch the risers.** Tier 2 ({{tier2}}) holds {{tier2_share:.0f}}% of the money. Among single countries, {{risers}} are growing at least ten points faster than the total. Check them against your own pipeline before committing.

**3. Do not depend on the Gulf alone.** It still sends {{gcc26:.0f}}% of the money, down from {{gcc20:.0f}}% in FY20. In FY26 it grew {{gcc_growth:+.1f}}% against {{growth_fy26:+.1f}}% overall, while Europe grew {{europe_growth:+.0f}}% and Asia-Pacific {{apac_growth:+.0f}}%; North America was flat ({{namerica_growth:+.1f}}%).

**4. Plan liquidity and campaigns around Eid.** Hold extra capacity for the {{window_days}} days before each Eid. For the next two Eids ({{next_eids}}), the indicative extra flow in the busiest month is about ${{cal_central_max:,.0f}} million at the central estimate and up to ${{cal_high_max:,.0f}} million at the top of the range (table below). Focus UK, USA and Oman marketing on that window.

**5. Use the quiet months.** {{weak_months}} are the weakest months, a natural time for onboarding drives and system changes.

**6. Measure your own flows.** These are national totals. A provider should repeat the analysis on its own transactions, where it can also see customers, prices and channels.

## Planning calendar

Indicative extra remittances against trend in each month the {{window_days}}-day window before Eid touches. The range is the 95% range of the estimate, so it is wide and includes zero. Eid dates are approximate and depend on the moon.

{{table_calendar}}

## What this analysis cannot tell you

- **Individual providers.** It describes the whole country, not one company's customers.
- **Informal channels.** Only remittances recorded by the central bank are counted.
- **Prices.** Exchange rates and fees are not modelled.
- **Recent months by country.** Monthly country data end in {{last_month}}.
- **Cause.** Associations only: {{event_list}}.

## Key numbers

The largest corridors, FY26:

{{table_corridors}}

Method, data and checks: [`docs/methodology.md`](methodology.md), [`docs/data_sources.md`](data_sources.md).
