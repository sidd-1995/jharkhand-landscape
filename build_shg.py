#!/usr/bin/env python3
"""Merge district/block-level SHG (Self Help Group) counts into model.json.

Source: `jh_shg_data.json` — district -> [{name, new, revived, prenrlm, total, members}],
scraped from the DAY-NRLM public MIS (preprodmis.lokos.in/shgOuterReports.do), which
publishes block-level SHG rollups (New/Revived/PreNRLM/Total + Total Member) per district.
Re-run `python3 fetch_shg.py` first if the source data needs refreshing (requires network).
"""
import json

CANON = json.load(open("model.json"))["canon"]
raw = json.load(open("jh_shg_data.json"))

# jh_shg_data.json keys already match the 24-name canon 1:1 (verified against DIST_CODES in fetch_shg.py)
assert set(raw.keys()) == set(CANON), f"district mismatch: {set(raw.keys()) ^ set(CANON)}"

model = json.load(open("model.json"))
tot_shg = tot_mem = 0
for d in CANON:
    blocks = sorted(raw[d], key=lambda b: -b["total"])
    dist_total = sum(b["total"] for b in blocks)
    dist_mem = sum(b["members"] for b in blocks)
    tot_shg += dist_total; tot_mem += dist_mem
    model["districts"][d]["shg"] = {
        "total": dist_total, "members": dist_mem,
        "new": sum(b["new"] for b in blocks),
        "revived": sum(b["revived"] for b in blocks),
        "prenrlm": sum(b["prenrlm"] for b in blocks),
        "blocks": blocks,
    }

json.dump(model, open("model.json", "w"), ensure_ascii=False, separators=(",", ":"))
print(f"SHG merged: {tot_shg} SHGs, {tot_mem} members across {len(CANON)} districts")
