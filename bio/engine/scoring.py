# -*- coding: utf-8 -*-
"""AI生命科学评分引擎：归一化 -> 加权 -> 线性映射(0-100) -> 蒙特卡洛 +/-1sigma。"""
import random
from config.indicators import INDICATORS

DIMS = list(INDICATORS.keys())
WEIGHTS = [v[0] for v in INDICATORS.values()]

def _clamp(x, lo=0.0, hi=100.0):
    return max(lo, min(hi, x))

def score_company(c, seed=None):
    raw = {d: float(c.get(d, 0.0)) for d in DIMS}
    total = sum(raw[d] * w for d, w in zip(DIMS, WEIGHTS))
    mapped = _clamp(10 + 0.85 * total)
    rng = random.Random(seed if seed is not None else id(c.get("id", "")))
    samples = [_clamp(mapped + rng.gauss(0, 2.0)) for _ in range(2000)]
    mean = sum(samples) / len(samples)
    var = sum((s - mean) ** 2 for s in samples) / len(samples)
    sd = var ** 0.5
    return {
        "id": c.get("id"), "name": c.get("name"), "country": c.get("country"),
        "track": c.get("track"), "role": c.get("role"), "market": c.get("market", ""),
        "dims": raw, "score": round(mean, 1), "lo": round(mean - sd, 1), "hi": round(mean + sd, 1),
    }

def score_all(companies):
    out = []
    for i, c in enumerate(companies):
        out.append(score_company(c, seed=hash(c.get("id", str(i))) % (2**32)))
    out.sort(key=lambda x: x["score"], reverse=True)
    return out
