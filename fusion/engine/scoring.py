# -*- coding: utf-8 -*-
"""可控核聚变评分引擎：归一化 -> 加权 -> 线性映射(0-100) -> 蒙特卡洛 +/-1sigma。"""
import random
from config.indicators import INDICATORS

DIMS = list(INDICATORS.keys())
WEIGHTS = [v[0] for v in INDICATORS.values()]

def _clamp(x, lo=0.0, hi=100.0):
    return max(lo, min(hi, x))

def score_company(c, seed=None):
    """c: dict with raw values per dimension (0-100 原始主观/近似打分). 返回 dict。"""
    raw = {d: float(c.get(d, 0.0)) for d in DIMS}
    # 加权总分 (0-100)
    total = sum(raw[d] * w for d, w in zip(DIMS, WEIGHTS))
    # 线性映射到 (10,95) 区间，避免满分/零分极端
    mapped = _clamp(10 + 0.85 * total)
    # 蒙特卡洛 N=2000 估计 +/-1 sigma
    rng = random.Random(seed if seed is not None else id(c.get("id", "")))
    samples = [mapped + rng.gauss(0, 2.0) for _ in range(2000)]
    samples = [_clamp(s) for s in samples]
    mean = sum(samples) / len(samples)
    var = sum((s - mean) ** 2 for s in samples) / len(samples)
    sd = var ** 0.5
    return {
        "id": c.get("id"), "name": c.get("name"), "country": c.get("country"),
        "route": c.get("route"), "role": c.get("role"),
        "dims": raw, "score": round(mean, 1), "lo": round(mean - sd, 1), "hi": round(mean + sd, 1),
    }

def score_all(companies):
    out = []
    for i, c in enumerate(companies):
        out.append(score_company(c, seed=hash(c.get("id", str(i))) % (2**32)))
    out.sort(key=lambda x: x["score"], reverse=True)
    return out
