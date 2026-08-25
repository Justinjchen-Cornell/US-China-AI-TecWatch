"""
Semiconductor Composite Index 计算引擎
========================================
输入: data/indicators.json + config/weights.json
输出: 综合指数(0-100, >50偏中国有利) + 六维分 + 暗线修正 + 不确定性区间
方法: 归一化 -> 维内几何平均 -> 加权sigmoid -> MC不确定性
"""
import json, math, os, random

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IND = os.path.join(BASE, "data", "indicators.json")
WGT = os.path.join(BASE, "config", "weights.json")


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def geo_mean(vals):
    # Laplace 平滑: 每个值映射到 (v*(hi-lo)+lo) 后取几何平均
    if not vals:
        return None
    logsum = 0.0
    for v in vals:
        logsum += math.log(max(v, 1e-6))
    return math.exp(logsum / len(vals))


def load():
    with open(IND, encoding="utf-8") as f:
        ind = json.load(f)
    with open(WGT, encoding="utf-8") as f:
        wgt = json.load(f)
    return ind, wgt


def dim_score(dim):
    """单维度几何平均分(0-1), 返回 (score01, n_indicators)"""
    vals = []
    for it in dim["indicators"]:
        v = clamp(it["value"] / 100.0)
        vals.append(v)
    return geo_mean(vals), len(vals)


def compute(seed=None):
    ind, wgt = load()
    rng = random.Random(seed if seed is not None else 42)

    dim_weights = wgt["dim_weights"]
    dl_weight = wgt.get("dark_line_weight", 0.5)
    scale = wgt.get("sigmoid_scale", 1.0)
    mc_n = int(wgt.get("mc_samples", 2000))

    # ---- 六维分（按指标展开，便于与 MC 统一加权）----
    dim_results = []
    zw = 0.0
    znum = 0.0
    for dim in ind["dimensions"]:
        s, n = dim_score(dim)
        w = dim_weights.get(dim["id"], dim.get("weight", 1.0))
        dim_results.append({
            "id": dim["id"],
            "name": dim["name"],
            "weight": w,
            "score01": round(s, 4),
            "score100": round(s * 100, 2),
            "n": n,
        })
        # 每个指标均摊维度权重: w/n，使 point 与 MC 尺度一致
        per = w / n if n else 0
        zw += per * n
        znum += (s - 0.5) * per * n

    # ---- 暗线修正 ----
    dl_list = ind.get("dark_lines", [])
    dl_contrib = 0.0
    dl_wtot = 0.0
    for dl in dl_list:
        v = clamp(dl["value"] / 100.0)
        dw = dl.get("weight", 0.5)
        dl_contrib += (v - 0.5) * dw
        dl_wtot += dw
    if dl_wtot > 0:
        dl_contrib = dl_contrib / dl_wtot * dl_weight  # 归一化后乘权重

    z = znum / zw + dl_contrib if zw > 0 else dl_contrib
    index = 100.0 / (1.0 + math.exp(-scale * z * 4.0))  # sigmoid, 放大系数4使区分度合理

    # ---- 蒙特卡洛不确定性（与 point estimate 完全同构）----
    samples = []
    for _ in range(mc_n):
        zz = 0.0
        zw2 = 0.0
        for dim in ind["dimensions"]:
            s = 0.0
            for it in dim["indicators"]:
                v = clamp(it["value"] / 100.0)
                noise = rng.gauss(0, 0.04 * (1.0 - it.get("source_reliability", 0.7)))
                vv = clamp(v + noise)
                s += math.log(max(vv, 1e-6))
            n = len(dim["indicators"])
            geo = math.exp(s / n) if n else 0.5
            w = dim_weights.get(dim["id"], dim.get("weight", 1.0))
            per = w / n if n else 0
            zw2 += per * n
            zz += (geo - 0.5) * per * n
        # 暗线扰动
        dl_c = 0.0
        dl_wtot2 = 0.0
        for dl in dl_list:
            v = clamp(dl["value"] / 100.0)
            noise = rng.gauss(0, 0.05 * (1.0 - dl.get("source_reliability", 0.7)))
            vv = clamp(v + noise)
            dw = dl.get("weight", 0.5)
            dl_c += (vv - 0.5) * dw
            dl_wtot2 += dw
        if dl_wtot2 > 0:
            zz = zz / zw2 + dl_c / dl_wtot2 * dl_weight
        else:
            zz = zz / zw2
        samples.append(100.0 / (1.0 + math.exp(-scale * zz * 4.0)))

    samples.sort()
    mean = sum(samples) / len(samples)
    sd = (sum((s - mean) ** 2 for s in samples) / len(samples)) ** 0.5
    lo = samples[int(0.158 * len(samples))]
    hi = samples[int(0.842 * len(samples))]

    # 数据置信度: 各指标source_reliability的几何平均
    rels = [it.get("source_reliability", 0.7) for d in ind["dimensions"] for it in d["indicators"]]
    data_conf = geo_mean(rels) if rels else 0.7

    return {
        "index": round(index, 2),
        "mc_mean": round(mean, 2),
        "mc_std": round(sd, 2),
        "ci_low": round(lo, 2),
        "ci_high": round(hi, 2),
        "data_confidence": round(data_conf * 100, 2),
        "dimensions": dim_results,
        "dark_lines": [
            {"name": dl["name"], "value": dl["value"], "weight": dl.get("weight", 0.5)}
            for dl in dl_list
        ],
        "n_indicators": sum(d["n"] for d in dim_results),
        "updated": ind.get("updated"),
    }


if __name__ == "__main__":
    r = compute()
    print(json.dumps(r, ensure_ascii=False, indent=2))
