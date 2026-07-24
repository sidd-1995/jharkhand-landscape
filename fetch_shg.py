#!/usr/bin/env python3
"""Fetch district/block-level SHG (Self Help Group) counts for Jharkhand from the
public DAY-NRLM MIS (preprodmis.lokos.in/shgOuterReports.do) and write jh_shg_data.json.

The MIS publishes block-level SHG rollups per district (New/Revived/PreNRLM/Total +
Total Member) with no login required. Re-run this only when the SHG figures need
refreshing (requires network); then re-run `build_shg.py` to merge into model.json.
"""
import re, json, time, sys, subprocess, urllib.parse

BASE = "https://preprodmis.lokos.in/shgOuterReports.do"

def fetch(params, retries=4):
    qs = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
    url = f"{BASE}?{qs}"
    for attempt in range(retries):
        try:
            result = subprocess.run(["curl", "-s", "-f", "--max-time", "30", url],
                                     capture_output=True, timeout=35)
            if result.returncode == 0:
                return result.stdout.decode("utf-8", errors="replace")
            raise RuntimeError(f"curl exit {result.returncode}")
        except Exception as e:
            if attempt == retries - 1:
                print(f"FAILED: {url} -> {e}", file=sys.stderr)
                return None
            time.sleep(2 * (attempt + 1))

DIST_CODES = {
    "Ranchi": "3401", "Lohardaga": "3402", "Gumla": "3403", "Simdega": "3404",
    "Palamu": "3405", "Latehar": "3406", "Garhwa": "3407", "West Singhbhum": "3408",
    "Saraikela-Kharsawan": "3409", "East Singhbhum": "3410", "Dumka": "3411",
    "Jamtara": "3412", "Sahibganj": "3413", "Pakur": "3414", "Godda": "3415",
    "Hazaribagh": "3416", "Chatra": "3417", "Koderma": "3418", "Giridih": "3419",
    "Bokaro": "3420", "Dhanbad": "3421", "Deoghar": "3422", "Ramgarh": "3423",
    "Khunti": "3424",
}

def get_blocks(dist_code):
    html = fetch({"methodName": "showBlockPage", "encd": dist_code,
                  "stateName": "JHARKHAND", "districtName": "X"})
    if not html:
        return []
    tbody_match = re.search(r"<tbody>(.*?)</tbody>", html, re.S)
    if not tbody_match:
        return []
    rows = []
    trs = re.findall(r"<tr>(.*?)</tr>", tbody_match.group(1), re.S)
    for tr in trs:
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        if len(tds) < 6:
            continue
        clean = lambda x: re.sub(r"<[^>]+>", "", x).strip().replace(",", "")
        vals = [clean(td) for td in tds]
        if not vals[0].isdigit():
            continue
        name_match = re.search(r">([^<]+)<", tds[1]) or re.search(r"'([^']+)'\s*\)\s*</a>|>([^<]*)$", tds[1])
        name = clean(re.sub(r"<a[^>]*>|</a>", "", tds[1]))
        try:
            new_, revived, prenrlm, total, members = (int(v) if v else 0 for v in vals[2:7])
        except ValueError:
            continue
        rows.append({"name": name, "new": new_, "revived": revived, "prenrlm": prenrlm,
                      "total": total, "members": members})
    return rows

if __name__ == "__main__":
    result = {}
    for dist, code in DIST_CODES.items():
        blocks = get_blocks(code)
        result[dist] = blocks
        tot = sum(b["total"] for b in blocks)
        mem = sum(b["members"] for b in blocks)
        print(f"{dist}: {len(blocks)} blocks, {tot} SHGs, {mem} members", file=sys.stderr)
        time.sleep(0.3)
    json.dump(result, open("jh_shg_data.json", "w"), indent=1)
    print("done")
