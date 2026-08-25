#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 indicators.json 生成本期快照 data/snapshots/YYYY-MM-DD.json。"""
import argparse, json, os, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--out-dir", default=os.path.join(ROOT,"data","snapshots"))
    args = ap.parse_args()
    ind = json.load(open(os.path.join(ROOT,"data","indicators.json"),"r",encoding="utf-8"))
    snap = {"date": args.date, "schema_version":1,
            "updated": ind.get("updated", args.date),
            "indicators": ind["indicators"]}
    os.makedirs(args.out_dir, exist_ok=True)
    out = os.path.join(args.out_dir, f"{args.date}.json")
    with open(out,"w",encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False, indent=2)
    print(f"[update_snapshot] {out}")
if __name__=="__main__":
    main()
