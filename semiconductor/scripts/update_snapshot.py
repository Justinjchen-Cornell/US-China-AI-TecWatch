"""
生成一期半导体综合指数快照，追加写入 data/history.json (时间序列)。
用法: python scripts/update_snapshot.py [--tag YYYY-MM-DD]
"""
import json, os, sys, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compute_index import compute

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.join(BASE, "data", "history.json")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default=None, help="快照日期标签 YYYY-MM-DD，默认取 indicators.updated")
    args = ap.parse_args()

    res = compute()
    tag = args.tag or res.get("updated") or "2026-08-24"
    rec = {
        "date": tag,
        "index": res["index"],
        "mc_mean": res["mc_mean"],
        "ci_low": res["ci_low"],
        "ci_high": res["ci_high"],
        "dimensions": {d["id"]: d["score100"] for d in res["dimensions"]},
    }
    history = []
    if os.path.exists(HIST):
        with open(HIST, encoding="utf-8") as f:
            history = json.load(f)
    history = [h for h in history if h.get("date") != tag]  # 同tag覆盖
    history.append(rec)
    history.sort(key=lambda x: x["date"])
    with open(HIST, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    print(f"[snapshot] {tag} index={rec['index']} (CI {rec['ci_low']}-{rec['ci_high']}) 共{len(history)}期")

if __name__ == "__main__":
    main()
