# Phase 2 VCG Verdict Baseline (Before)

Captured 2026-08-29, branch `phase2-vcg-real-check`. This is the "before" state against which all Phase 2 verdict deltas are measured.

## VCG Per-Entry Verdict Table (33 entries)

| Paper ID | Verdict | Entry-Specific |
|----------|---------|---|
| 2404_13841 | VERIFIED | True |
| 2504_05563 | VERIFIED | True |
| 3626307_3626311 | VERIFIED | True |
| Ahmed2023frimfl | VERIFIED_TEMPLATE | False |
| Batool2022fl_mab | VERIFIED_TEMPLATE | False |
| Cheng2022uav | VERIFIED | True |
| Cong2020vcg | VERIFIED | True |
| Cui2024auction_market | VERIFIED_TEMPLATE | False |
| Deng2020fmore_auction | VERIFIED | True |
| GPS2023afl_recruit | VERIFIED_TEMPLATE | False |
| Haupt2021auctions | VERIFIED | True |
| Jiao2019auto_auction | VERIFIED | True |
| Jin2023bara_budget | VERIFIED | True |
| Le2021cellular_auction | VERIFIED | True |
| Lim2020edge_collab | VERIFIED_TEMPLATE | False |
| Liu2023reverse_auction | VERIFIED | True |
| Lu2021cluster_auction | VERIFIED_TEMPLATE | False |
| Mai2022double_auction | VERIFIED_TEMPLATE | False |
| Model2024trading_fl | VERIFIED | True |
| Ng2020uav_auction_coalition | VERIFIED | True |
| Peng2023auction_medical | VERIFIED_TEMPLATE | False |
| Seo2021sdn_fl | VERIFIED_TEMPLATE | False |
| Seo2022noniid_auction | VERIFIED_TEMPLATE | False |
| Tan2023hire | VERIFIED_TEMPLATE | False |
| Tan2025longterm | VERIFIED | True |
| Wei2024truthful_bandit | VERIFIED_TEMPLATE | False |
| Xia2026privacy_mfg | VERIFIED | True |
| Xiang2025esr_mhfl | VERIFIED | True |
| Yang2023buyers_market | VERIFIED_TEMPLATE | False |
| Zhang2022expost_auction | VERIFIED | True |
| Zhang2022online | VERIFIED | True |
| Zhang2024auction_comm | VERIFIED | True |
| Zheng2023fl_market | VERIFIED_TEMPLATE | False |

**VCG Verdict Summary:**
- VERIFIED (entry-specific): 19
- VERIFIED_TEMPLATE: 14
- Total: 33

## Corpus Summary

```
================================================================
  Multi-Track Verification Summary  (105 entries checked)
================================================================
  VERIFIED           (25)
  VERIFIED_TEMPLATE  (73)
  UNKNOWN            (2)
  UNSUPPORTED        (5)
  ├─ Passed (98 total, 25 entry-specific):
  │   VCG (33): 19 form-confirmed, 14 template-only
  │   Contract entry-specific (LaTeX utility):   5
  │   Contract template (linear-cost model):     31
  │   SOS certificate (Track 2, poly degree≥2):  4
  │   Bayesian IC (Track 4, symbolic integral):  1
  └─ Stackelberg equilibrium IR (NOT DSIC): 29 (1 entry-specific, 28 template-only)
  dReal δ-verified (Track 3, transcendental):   1
================================================================
```

## Test Suite Status

```
176 passed, 5 xfailed in 19.57s
```

All tests green. No failures.
