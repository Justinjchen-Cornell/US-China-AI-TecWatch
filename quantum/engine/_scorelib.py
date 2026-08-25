# -*- coding: utf-8 -*-
"""量子计算产业投资分析 —— 六维评分核心库（独立、可复算）。

算法：
  1) 各指标线性归一化到 [0,1]（按各维度独立 min/max）；
  2) 维度内几何平均（Laplace 平滑 eps=1，避免 0 值）；
  3) 六维按 WEIGHTS 加权求和 -> z；
  4) 综合得分 = 100 * z / z_max，稳定落在 (0,100)；
  5) 蒙特卡洛 N=2000 对各指标加噪声，给出 ±1σ 置信区间。
"""
import json
import numpy as np
from pathlib import Path
from config.indicators import DIMENSIONS, WEIGHTS

EPS = 1.0
N_MC = 2000


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def normalize(snapshot):
    """对单期快照做维度归一化，返回 {dim: 0-1 标量}。"""
    out = {}
    for dim in DIMENSIONS:
        raw = snapshot.get("indicators", {}).get(dim, [])
        if not raw:
            out[dim] = 0.0
            continue
        vals = [float(x["value"]) for x in raw]
        lo, hi = min(vals), max(vals)
        if hi - lo < 1e-9:
            out[dim] = max(0.0, min(1.0, vals[0] / 100.0))
        else:
            out[dim] = (sum(vals) / len(vals) - lo) / (hi - lo)
    return out


def dim_score(norm_dim):
    """维度内几何平均（Laplace 平滑）。"""
    vals = np.array([norm_dim[d] for d in DIMENSIONS], dtype=float) + EPS
    return float(np.exp(np.mean(np.log(vals))) - EPS)


def composite(norm_dim):
    """加权合成 -> 综合得分 (0-100)，线性映射，直观可复算。"""
    z = 0.0
    wsum = 0.0
    for d in DIMENSIONS:
        z += WEIGHTS[d] * norm_dim[d]
        wsum += WEIGHTS[d]
    z /= wsum
    return float(100.0 * z)


def confidence_interval(snapshot, seed=42):
    """蒙特卡洛置信区间（±1σ）。"""
    rng = np.random.default_rng(seed)
    norm = normalize(snapshot)
    base = composite(norm)
    samples = []
    for _ in range(N_MC):
        noisy = {}
        for d in DIMENSIONS:
            noise = rng.normal(0, 0.05)
            noisy[d] = float(np.clip(norm[d] + noise, 0, 1))
        samples.append(composite(noisy))
    samples = np.array(samples)
    std = float(samples.std())
    return base, max(0.0, base - std), min(100.0, base + std)


def score_snapshot(snapshot):
    """对一份快照（单期指标）输出完整评分字典。"""
    norm = normalize(snapshot)
    base, lo, hi = confidence_interval(snapshot)
    return {
        "name": snapshot.get("name", "Quantum Index"),
        "date": snapshot.get("date", ""),
        "dim_norm": {d: round(float(norm[d]), 4) for d in DIMENSIONS},
        "dim_score": round(dim_score(norm), 2),
        "composite": round(base, 2),
        "ci_low": round(lo, 2),
        "ci_high": round(hi, 2),
    }


def score_company(company):
    """对公司单条记录（indicators 为 {dim: 0-100}）计算得分。"""
    ind = company.get("indicators", {}) or {}
    dims = {d: float(ind[d]) for d in DIMENSIONS if d in ind}
    if not dims:
        return {"name": company.get("name"), "composite": 0.0,
                "ci_low": 0.0, "ci_high": 0.0}
    avg = sum(dims.values()) / len(dims)
    snap = {
        "name": company.get("name"), "date": "",
        "indicators": {d: [{"value": v}] for d, v in dims.items()},
    }
    s = score_snapshot(snap)
    return {"name": company.get("name"), "composite": round(avg, 2),
            "ci_low": s["ci_low"], "ci_high": s["ci_high"]}
