#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compute_index.py —— 中美 AI 竞争综合指数 (AICompete Index) 计算引擎

方法:
  1) 每指标按 direction 做 0-1 归一化 (正向线性 / 反向取补 / 比率对数缩放)
  2) 每维内指标取几何平均 (Laplace 平滑) -> 维度分
  3) 维度分按权重加权 -> z -> sigmoid -> Index ∈ (0,100)
  4) 蒙特卡洛 (N=mc_samples) 对指标值按 ±source_reliability 扰动,
     输出 index_low / index_high (±1σ) 与 confidence (加权平均可靠度)
"""
import argparse, json, os, math, statistics, random
from copy import deepcopy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SNAPSHOT = os.path.join(ROOT, "data", "snapshots", "2026-08-24.json")

def load_json(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def norm(value, direction, ref_max, ref_min=0.0, eps=1e-6):
    """归一化到 [0,1]: 正向指标越高越好; 反向越低越好。"""
    if value is None:
        return None
    v = float(value)
    if ref_max == ref_min:
        s = 0.5
    else:
        s = (v - ref_min) / (ref_max - ref_min)
        s = max(0.0, min(1.0, s))
    if direction == -1:  # 反向: 值越大越不利 -> 取补
        s = 1.0 - s
    return max(0.0, min(1.0, s))

def geo_mean(vals, eps=1e-3):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    log_sum = sum(math.log(v + eps) for v in vals)
    return math.exp(log_sum / len(vals))

def dim_score(indicators, dim, eps=1e-3):
    vals = []
    for ind in indicators:
        if ind.get("dim") != dim:
            continue
        v = ind.get("norm")
        if v is not None:
            vals.append(v)
    return geo_mean(vals, eps)

def compute(snapshot, weights_cfg):
    indicators = deepcopy(snapshot["indicators"])
    dims = weights_cfg["dimensions"]
    params = weights_cfg.get("params", {})
    eps = params.get("laplace_epsilon", 1e-3)
    mc = int(params.get("mc_samples", 2000))
    scale = float(params.get("sigmoid_scale", 4.0))
    target = float(params.get("index_target", 50))

    # --- 归一化: 先按维度收集 min/max 作为归一化参考 ---
    by_dim = {}
    for ind in indicators:
        by_dim.setdefault(ind["dim"], []).append(ind)
    for dim, inds in by_dim.items():
        vals = [float(i["value"]) for i in inds if i.get("value") is not None]
        vmin, vmax = (min(vals), max(vals)) if vals else (0.0, 1.0)
        if vmax == vmin:
            vmax = vmin + 1.0
        for i in inds:
            i["norm"] = norm(i.get("value"), i.get("direction", 1), vmax, vmin, eps)

    # --- 维度分 ---
    dim_scores = {}
    for d in dims:
        dim_scores[d] = dim_score(indicators, d, eps)

    # --- 加权 z (含暗线修正) ---
    w_total = sum(dims[d]["weight"] for d in dims if dim_scores.get(d) is not None)
    z = 0.0
    rel_sum = 0.0
    for d, sc in dim_scores.items():
        if sc is None:
            continue
        w = dims[d]["weight"]
        z += w * (sc - 0.5)
        rel_sum += w * float(inds_reliability(indicators, d))
    # 暗线修正项
    lat = weights_cfg.get("latent_factors", {})
    lat_sig = weights_cfg.get("latent_signals", {})
    lat_w = 0.0
    for k, cfg in lat.items():
        sig = lat_sig.get(k, 0.5)
        lat_w += cfg["weight"] * (sig - 0.5)
    z += lat_w
    w_total += sum(cfg["weight"] for cfg in lat.values())

    if w_total > 0:
        confidence = (rel_sum + sum(cfg["weight"]*0.7 for cfg in lat.values())) / w_total
    else:
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))

    # --- sigmoid 综合指数 ---
    z_std = z / scale
    index_val = 100.0 / (1.0 + math.exp(-z_std))
    # 以 target=50 为中心, 把 z=0 映射到 target
    index_val = target + (index_val - 50.0)  # 线性平移, 保持单调

    # --- 蒙特卡洛 置信区间 ---
    samples = []
    for _ in range(mc):
        zz = 0.0
        for d, sc in dim_scores.items():
            if sc is None: continue
            w = dims[d]["weight"]
            noise = random.gauss(0, 1) * 0.05  # ±5% 扰动
            zz += w * ((sc - 0.5) * (1 + noise))
        zz += lat_w
        zz_std = zz / scale
        iv = target + (100.0 / (1.0 + math.exp(-zz_std)) - 50.0)
        samples.append(iv)
    low = statistics.mean(s - statistics.stdev(samples) for s in [statistics.mean(samples)]) if len(samples)>1 else index_val
    high = statistics.mean(samples) + statistics.stdev(samples) if len(samples)>1 else index_val
    low = max(0.0, min(100.0, low))
    high = max(0.0, min(100.0, high))
    mean_s = statistics.mean(samples)

    return {
        "index": round(index_val, 1),
        "index_mean": round(mean_s, 1),
        "index_low": round(low, 1),
        "index_high": round(high, 1),
        "confidence": round(confidence, 3),
        "dimension_scores": {d: round(v, 3) if v is not None else None for d,v in dim_scores.items()},
        "indicators": indicators,
        "mc_samples": mc,
    }

def inds_reliability(indicators, dim):
    rels = [float(i.get("source_reliability", 0.7)) for i in indicators if i.get("dim")==dim]
    return sum(rels)/len(rels) if rels else 0.7

def main():
    ap = argparse.ArgumentParser(description="计算中美AI竞争综合指数")
    ap.add_argument("--snapshot", default=DEFAULT_SNAPSHOT, help="快照 JSON 路径")
    ap.add_argument("--out", default=None, help="输出 result JSON 路径 (默认打印)")
    args = ap.parse_args()

    snap = load_json(args.snapshot)
    weights_cfg = load_json(os.path.join(ROOT, "config", "weights.json"))
    result = compute(snap, weights_cfg)
    result["snapshot_date"] = snap.get("date") or snap.get("updated") or ""
    result["schema_version"] = 1
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(payload)
        print(f"[compute_index] 已写入 {args.out}")
    else:
        print(payload)

if __name__ == "__main__":
    main()
