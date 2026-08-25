# -*- coding: utf-8 -*-
"""
AI 大模型生态投资体系 · 综合评分引擎
====================================
输入：公司指标原始值 dict{indicator_id: raw_value}
输出：综合得分(0-100)、各维度分、归一化明细、置信区间
方法：
  1) 线性归一化到 [0,1]（higher_better / lower_better）
  2) 维度内按权重几何平均（Laplace 平滑避免 0）
  3) 全局按 DIMENSION_WEIGHTS 加权
  4) sigmoid 映射至 (0,100)
  5) 基于 source_reliability 做蒙特卡洛(N=2000) 得 ±1σ 区间
"""
import numpy as np
from config.indicators import (
    INDICATORS, DIMENSIONS, DIMENSION_WEIGHTS,
    NORMALIZATION_BOUNDS,
)


def normalize(raw, indicator_id):
    """线性归一化到 [0,1]，越有利越接近1。"""
    spec = next(i for i in INDICATORS if i["id"] == indicator_id)
    lo, hi = NORMALIZATION_BOUNDS[indicator_id]
    span = hi - lo
    if span <= 0:
        return 0.5
    x = (raw - lo) / span
    x = max(0.0, min(1.0, x))
    if spec["direction"] == "lower_better":
        x = 1.0 - x
    return x


def dim_score(raw_map, dim):
    """某维度内各指标归一化后按权重几何平均（Laplace 平滑）。"""
    inds = [i for i in INDICATORS if i["dim"] == dim]
    logs = []
    wsum = 0.0
    for i in inds:
        raw = raw_map.get(i["id"])
        if raw is None:
            continue
        n = normalize(raw, i["id"])
        w = i["weight_in_dim"]
        # Laplace 平滑: (n+1)/(1+1) 映射到 (0.5,1) 区间再取 log
        n_smooth = (n + 1.0) / (1.0 + 1.0)  # (0,1) -> (0.5,1)
        logs.append(np.log(n_smooth) * w)
        wsum += w
    if wsum == 0:
        return None
    geom = np.exp(sum(logs) / wsum)
    # 反平滑还原到 [0,1]
    return max(0.0, min(1.0, 2.0 * geom - 1.0))


def composite(raw_map, mc_samples=2000, seed=42):
    """计算综合得分及置信区间。"""
    rng = np.random.default_rng(seed)
    dim_vals = {}
    rels = []
    for dim in DIMENSIONS:
        v = dim_score(raw_map, dim)
        if v is not None:
            dim_vals[dim] = v
            rels.append(next(i["source_reliability"] for i in INDICATORS if i["dim"] == dim))
    if not dim_vals:
        return {"score": 50.0, "dim_scores": {}, "ci_low": 50.0, "ci_high": 50.0,
                "confidence": 0.0, "normalized": {}}
    # 加权合成
    wsum = sum(DIMENSION_WEIGHTS[d] for d in dim_vals)
    z = sum(DIMENSION_WEIGHTS[d] / wsum * dim_vals[d] for d in dim_vals)
    # sigmoid 映射
    score = 100.0 / (1.0 + np.exp(-6.0 * (z - 0.5)))
    # 蒙特卡洛：按 source_reliability 扰动归一化值
    noise_scale = 0.15 * (1.0 - np.mean(rels)) if rels else 0.10
    samples = []
    for _ in range(mc_samples):
        zp = z + rng.normal(0, max(noise_scale, 0.02))
        zp = max(0.0, min(1.0, zp))
        samples.append(100.0 / (1.0 + np.exp(-6.0 * (zp - 0.5))))
    samples = np.array(samples)
    ci_low = float(np.percentile(samples, 15.8))
    ci_high = float(np.percentile(samples, 84.2))
    confidence = float(np.mean(rels)) if rels else 0.5
    normalized = {}
    for i in INDICATORS:
        if raw_map.get(i["id"]) is not None:
            normalized[i["id"]] = normalize(raw_map[i["id"]], i["id"])
    return {
        "score": float(score),
        "dim_scores": {d: float(v) for d, v in dim_vals.items()},
        "ci_low": ci_low, "ci_high": ci_high,
        "confidence": confidence,
        "normalized": normalized,
    }
