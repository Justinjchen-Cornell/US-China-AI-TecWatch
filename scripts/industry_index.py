#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
industry_index.py —— 行业客观指数计算器 (Objective Industry Index)

输入: 行业子目录下的 data/industry_indicators.json
      [{"id","name","value","direction","ref_min","ref_max","log_scale?","source_reliability","source","note?"}]
方法: 与主站 AICompete 同构:
  1) 按 ref_min/ref_max 线性/对数归一化到 [0,1] (direction=-1 取补)
  2) 指标级几何平均 (Laplace 平滑) -> 行业分
  3) sigmoid -> index ∈ (0,100), >50 中国相对有利
  4) 蒙特卡洛 (N=2000) ±1σ -> low/high; confidence = 加权平均可靠度

所有指标值随 latest.json 发布, 任何人可复算。
"""
import argparse, json, os, math, statistics, random

def geo_mean(vals, eps=1e-3):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    return math.exp(sum(math.log(v + eps) for v in vals) / len(vals))

def compute(indicators, mc=2000, scale=4.0, target=50.0):
    norms, rels = [], []
    for ind in indicators:
        v = ind.get("value")
        if v is None:
            continue
        v = float(v)
        lo, hi = float(ind["ref_min"]), float(ind["ref_max"])
        if ind.get("log_scale"):
            s = math.log(1.0 + max(0.0, v - lo)) / math.log(1.0 + (hi - lo))
        elif hi != lo:
            s = (v - lo) / (hi - lo)
        else:
            s = 0.5
        s = max(0.0, min(1.0, s))
        if int(ind.get("direction", 1)) == -1:
            s = 1.0 - s
        norms.append(s)
        rels.append(float(ind.get("source_reliability", 0.7)))
    if not norms:
        return None
    score = geo_mean(norms)
    z = math.log(max(score, 1e-6) / max(1 - score, 1e-6)) / scale  # logit with scale
    index_val = target + (100.0 / (1.0 + math.exp(-z)) - 50.0)
    samples = []
    for _ in range(mc):
        nz = [max(0.0, min(1.0, n + random.gauss(0, 1) * 0.05)) for n in norms]
        sc = geo_mean(nz)
        zz = math.log(max(sc, 1e-6) / max(1 - sc, 1e-6)) / scale
        samples.append(target + (100.0 / (1.0 + math.exp(-zz)) - 50.0))
    mean = statistics.mean(samples)
    sd = statistics.stdev(samples) if len(samples) > 1 else 0.0
    return {
        "index": round(index_val, 1),
        "index_low": round(max(0.0, mean - sd), 1),
        "index_high": round(min(100.0, mean + sd), 1),
        "confidence": round(sum(rels) / len(rels), 3),
        "n_indicators": len(norms),
        "industry_score01": round(score, 4),
        "indicators": [{"id": i["id"], "name": i["name"], "value": i.get("value"),
                        "norm": round(norms[k], 4) if k < len(norms) else None,
                        "direction": i.get("direction", 1), "source": i.get("source", ""),
                        "source_reliability": i.get("source_reliability", 0.7)}
                       for k, i in enumerate(indicators) if i.get("value") is not None],
    }

def main():
    ap = argparse.ArgumentParser(description="行业客观指数计算器")
    ap.add_argument("--indicators", required=True, help="industry_indicators.json 路径")
    ap.add_argument("--out", default=None, help="输出 JSON (默认打印)")
    args = ap.parse_args()
    data = json.load(open(args.indicators, encoding="utf-8"))

    res = compute(data["indicators"])
    res["industry"] = data.get("industry", "")
    res["industry_cn"] = data.get("industry_cn", "")
    res["as_of"] = data.get("as_of", "")

    # 历史序列: 用 series 中的 values 覆盖当前值重算 (支持回溯趋势)
    series = []
    for pt in data.get("series", []):
        inds_hist = []
        for ind in data["indicators"]:
            i = dict(ind)
            if pt.get("values", {}).get(ind["id"]) is not None:
                i["value"] = pt["values"][ind["id"]]
            inds_hist.append(i)
        r = compute(inds_hist)
        series.append({"as_of": pt["as_of"],
                       "index": r["index"],
                       "index_low": r["index_low"],
                       "index_high": r["index_high"],
                       "confidence": r["confidence"]})
    res["series"] = series

    payload = json.dumps(res, ensure_ascii=False, indent=2)
    if args.out:
        open(args.out, "w", encoding="utf-8").write(payload)
        print(f"[industry_index] 已写入 {args.out}")
    else:
        print(payload)

if __name__ == "__main__":
    main()
