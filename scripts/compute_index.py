#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compute_index.py —— 中美 AI 竞争综合指数 (AICompete Index) 计算引擎

方法:
  1) 每指标按 direction 做 0-1 归一化:
     - 优先用指标定义中的绝对参考区间 ref_min/ref_max (跨快照稳定, 单指标维度不失真)
     - 比率/规模类指标可开 log_scale: s = log(1+x)/log(1+x_max)
     - 未配置参考区间时回退到维度内 min/max (min==max 时取中性 0.5)
     - 反向指标 (direction=-1) 取补
  2) 每维内指标取几何平均 (Laplace 平滑) -> 维度分
  3) 维度分按权重加权 -> z -> sigmoid -> Index ∈ (0,100)
  4) 暗线信号: 若指标带 latent 标签, 由该组指标归一化值的几何平均推导;
     无对应数据时回退到 config/latent_signals 中的配置值
  5) 蒙特卡洛 (N=mc_samples) 对指标值按 ±source_reliability 扰动,
     输出 index_low / index_high (±1σ) 与 confidence (加权平均可靠度)
"""
import argparse, json, os, math, statistics, random
from copy import deepcopy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SNAPSHOT = os.path.join(ROOT, "data", "snapshots", "2026-08-24.json")

def load_json(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def norm(ind, dim_min, dim_max, eps=1e-6):
    """归一化到 [0,1]。ref_min/ref_max 优先；否则回退维度内 min/max。"""
    v = ind.get("value")
    if v is None:
        return None
    v = float(v)
    direction = ind.get("direction", 1)
    ref_min = ind.get("ref_min")
    ref_max = ind.get("ref_max")
    if ref_min is not None and ref_max is not None:
        lo, hi = float(ref_min), float(ref_max)
        if ind.get("log_scale"):
            s = math.log(1.0 + max(0.0, v - lo)) / math.log(1.0 + (hi - lo))
        elif hi != lo:
            s = (v - lo) / (hi - lo)
        else:
            s = 0.5
    else:
        if dim_max == dim_min:
            s = 0.5
        else:
            s = (v - dim_min) / (dim_max - dim_min)
    s = max(0.0, min(1.0, s))
    if direction == -1:          # 反向: 值越大越不利 -> 取补
        s = 1.0 - s
    return max(0.0, min(1.0, s))

def geo_mean(vals, eps=1e-3):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    log_sum = sum(math.log(v + eps) for v in vals)
    return math.exp(log_sum / len(vals))

def dim_score(indicators, dim, eps=1e-3):
    vals = [i.get("norm") for i in indicators if i.get("dim") == dim and i.get("norm") is not None]
    return geo_mean(vals, eps)

def inds_reliability(indicators, dim=None, latent=None):
    rels = [float(i.get("source_reliability", 0.7)) for i in indicators
            if (dim is not None and i.get("dim") == dim) or
               (latent is not None and i.get("latent") == latent)]
    return sum(rels) / len(rels) if rels else 0.7

def overlay_defs(snapshot_indicators, defs_by_id):
    """把指标定义 (参考区间/对数缩放/暗线标签/方向/可靠度) 叠加到快照观测值上。
    定义属于 config 层, 快照只存观测; 保证历史快照用最新定义重算一致。"""
    out = []
    for ind in snapshot_indicators:
        i = deepcopy(ind)
        d = defs_by_id.get(i.get("id"), {})
        for k in ("dim", "direction", "source_reliability", "source",
                  "ref_min", "ref_max", "log_scale", "latent", "name", "unit", "higher_better"):
            if d.get(k) is not None:
                i[k] = d[k]
        out.append(i)
    return out

def compute(snapshot, weights_cfg, defs_by_id=None):
    indicators = overlay_defs(snapshot["indicators"], defs_by_id or {})
    dims = weights_cfg["dimensions"]
    params = weights_cfg.get("params", {})
    eps = params.get("laplace_epsilon", 1e-3)
    mc = int(params.get("mc_samples", 2000))
    scale = float(params.get("sigmoid_scale", 4.0))
    target = float(params.get("index_target", 50))

    # --- 归一化: 先收集维度内 min/max 作为无 ref 指标的回退参考 ---
    by_dim = {}
    for ind in indicators:
        by_dim.setdefault(ind["dim"], []).append(ind)
    dim_bounds = {}
    for dim, inds in by_dim.items():
        vals = [float(i["value"]) for i in inds if i.get("value") is not None]
        dim_bounds[dim] = (min(vals), max(vals)) if vals else (0.0, 1.0)
    for ind in indicators:
        dmin, dmax = dim_bounds.get(ind["dim"], (0.0, 1.0))
        ind["norm"] = norm(ind, dmin, dmax, eps)

    # --- 维度分 ---
    dim_scores = {d: dim_score(indicators, d, eps) for d in dims}

    # --- 暗线信号: 有指标数据则由数据推导, 否则用配置默认值 ---
    lat_cfg = weights_cfg.get("latent_factors", {})
    lat_default = weights_cfg.get("latent_signals", {})
    lat_scores = {}
    lat_rel = {}
    for k, cfg in lat_cfg.items():
        inds = [i for i in indicators if i.get("latent") == k]
        norms = [i.get("norm") for i in inds if i.get("norm") is not None]
        if norms:
            lat_scores[k] = geo_mean(norms, eps)          # 数据驱动
            lat_rel[k] = inds_reliability(indicators, latent=k)
        else:
            lat_scores[k] = float(lat_default.get(k, 0.5))  # 回退配置
            lat_rel[k] = 0.7

    # --- 加权 z (六维 + 暗线修正) ---
    w_total = 0.0
    z = 0.0
    rel_sum = 0.0
    for d, sc in dim_scores.items():
        if sc is None:
            continue
        w = dims[d]["weight"]
        z += w * (sc - 0.5)
        rel_sum += w * float(inds_reliability(indicators, dim=d))
        w_total += w
    lat_w = 0.0
    for k, cfg in lat_cfg.items():
        sig = lat_scores[k]
        lat_w += cfg["weight"] * (sig - 0.5)
    z += lat_w
    w_total += sum(cfg["weight"] for cfg in lat_cfg.values())
    rel_sum += sum(cfg["weight"] * lat_rel[k] for k, cfg in lat_cfg.items())

    confidence = rel_sum / w_total if w_total > 0 else 0.0
    confidence = max(0.0, min(1.0, confidence))

    # --- sigmoid 综合指数 (以 target=50 为中心) ---
    index_val = target + (100.0 / (1.0 + math.exp(-z / scale)) - 50.0)

    # --- 蒙特卡洛 置信区间 ---
    samples = []
    for _ in range(mc):
        zz = 0.0
        for d, sc in dim_scores.items():
            if sc is None:
                continue
            w = dims[d]["weight"]
            noise = random.gauss(0, 1) * 0.05  # ±5% 扰动
            zz += w * ((sc - 0.5) * (1 + noise))
        zz += lat_w
        iv = target + (100.0 / (1.0 + math.exp(-zz / scale)) - 50.0)
        samples.append(iv)
    mean_s = statistics.mean(samples)
    sd = statistics.stdev(samples) if len(samples) > 1 else 0.0
    low = max(0.0, min(100.0, mean_s - sd))
    high = max(0.0, min(100.0, mean_s + sd))

    return {
        "index": round(index_val, 1),
        "index_mean": round(mean_s, 1),
        "index_low": round(low, 1),
        "index_high": round(high, 1),
        "confidence": round(confidence, 3),
        "dimension_scores": {d: round(v, 3) if v is not None else None for d, v in dim_scores.items()},
        "latent_scores": {k: round(v, 3) for k, v in lat_scores.items()},
        "latent_reliability": {k: round(v, 3) for k, v in lat_rel.items()},
        "indicators": indicators,
        "mc_samples": mc,
    }

def main():
    ap = argparse.ArgumentParser(description="计算中美AI竞争综合指数")
    ap.add_argument("--snapshot", default=DEFAULT_SNAPSHOT, help="快照 JSON 路径")
    ap.add_argument("--out", default=None, help="输出 result JSON 路径 (默认打印)")
    args = ap.parse_args()

    snap = load_json(args.snapshot)
    weights_cfg = load_json(os.path.join(ROOT, "config", "weights.json"))
    defs = load_json(os.path.join(ROOT, "data", "indicators.json"))
    defs_by_id = {i["id"]: i for i in defs["indicators"]}
    result = compute(snap, weights_cfg, defs_by_id)
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
