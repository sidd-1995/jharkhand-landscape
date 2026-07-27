#!/usr/bin/env python3
"""Merge district-level FPO (Farmer Producer Organisation) counts into model.json.

Source: `jh_fpo_data.json` -- district -> {fpos, shareholders, complete_financials},
from the FPO Platform (district-level only; no block-level breakdown available).
"""
import json

CANON = json.load(open("model.json"))["canon"]
raw = json.load(open("jh_fpo_data.json"))

assert set(raw.keys()) == set(CANON), f"district mismatch: {set(raw.keys()) ^ set(CANON)}"

model = json.load(open("model.json"))
for d in CANON:
    model["districts"][d]["fpo"] = raw[d]

json.dump(model, open("model.json", "w"), ensure_ascii=False, separators=(",", ":"))
tot_fpo = sum(v["fpos"] for v in raw.values())
tot_sh = sum(v["shareholders"] for v in raw.values())
print(f"FPO merged: {tot_fpo} FPOs, {tot_sh} shareholders across {len(CANON)} districts")
