# -*- coding: utf-8 -*-
"""量子计算产业投资分析 —— 梯队划分与配置建议。"""
from engine.scoring import score_company, DIMENSIONS
from config.indicators import DIM_LABEL


def tier_of(score):
    if score >= 55:
        return "领跑"
    if score >= 42:
        return "跟进"
    if score >= 30:
        return "潜力"
    return "观察"


def allocation_tags(company, score):
    """根据市场/商业化/路线属性生成配置标签。"""
    tags = []
    market = company.get("market", "")
    if "上市" in market or "IPO" in market:
        tags.append("确定性核心(已上市/流动性好)")
    else:
        tags.append("高弹性期权(一级市场/Pre-IPO)")
    if company.get("role") in ("整机/系统", "整机"):
        tags.append("整机赛道(技术路线博弈)")
    else:
        tags.append("卖铲人/部件(确定性较高)")
    return tags


def analyze_companies(companies):
    """对公司池打分、排序、分组。"""
    rows = []
    for c in companies:
        if not c.get("indicators"):
            continue
        s = score_company(c)
        row = {
            "name": c.get("name"),
            "country": c.get("country", ""),
            "route": c.get("route", ""),
            "role": c.get("role", ""),
            "market": c.get("market", ""),
            "valuation": c.get("valuation", ""),
            "score": s["composite"],
            "ci_low": s["ci_low"],
            "ci_high": s["ci_high"],
            "dim_norm": s.get("dim_norm", {}),
            "tier": tier_of(s["composite"]),
            "tags": allocation_tags(c, s["composite"]),
        }
        rows.append(row)
    rows.sort(key=lambda r: r["score"], reverse=True)
    grouped = {"领跑": [], "跟进": [], "潜力": [], "观察": []}
    for r in rows:
        grouped.setdefault(r["tier"], []).append(r)
    return rows, grouped


def build_report(snapshot, companies):
    """组装 latest.json 所需的全部 payload。"""
    from engine.scoring import score_snapshot, DIMENSIONS
    idx = score_snapshot(snapshot)
    rows, grouped = analyze_companies(companies)
    dim_avg = {}
    snap_ind = snapshot.get("indicators", {}) or {}
    for d in DIMENSIONS:
        raw = snap_ind.get(d, [])
        if raw:
            dim_avg[d] = round(float(raw[0]["value"]), 1)
        else:
            vs = [r["dim_norm"].get(d, 0) for r in rows]
            dim_avg[d] = round(100 * sum(vs) / len(vs), 1) if vs else 0.0
    return {
        "name": idx["name"],
        "date": idx["date"],
        "composite": idx["composite"],
        "ci_low": idx["ci_low"],
        "ci_high": idx["ci_high"],
        "dim_average": dim_avg,
        "dim_label": DIM_LABEL,
        "companies": rows,
        "tiers": grouped,
        "allocation": {
            "核心仓(已上市/卖铲人)": [r["name"] for r in rows if "确定性核心" in r["tags"]][:6],
            "期权仓(一级/整机前沿)": [r["name"] for r in rows if "高弹性期权" in r["tags"]][:6],
        },
    }
