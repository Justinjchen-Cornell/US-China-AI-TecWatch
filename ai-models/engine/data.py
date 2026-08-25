# -*- coding: utf-8 -*-
"""
AI 大模型生态投资体系 · 数据访问层
====================================
- 从 data/companies.json 读取公司基本面（名称/阵营/赛道/估值/ARR/上市状态等）
- 从 data/snapshots/*.json 读取各期指标快照
- 调用 scoring 计算综合得分，汇总为 latest / series
"""
import json, os
from datetime import date
from engine.scoring import composite

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPANIES_F = os.path.join(BASE, "data", "companies.json")
SNAP_DIR = os.path.join(BASE, "data", "snapshots")


def load_companies():
    with open(COMPANIES_F, encoding="utf-8") as f:
        return json.load(f)


def load_snapshot(asof=None):
    """读取指定期快照；默认读取最新一期（按文件名日期排序）。"""
    files = sorted([f for f in os.listdir(SNAP_DIR) if f.endswith(".json")])
    if not files:
        return None
    target = asof + ".json" if asof else files[-1]
    path = os.path.join(SNAP_DIR, target if target in files else files[-1])
    with open(path, encoding="utf-8") as f:
        return json.load(f), os.path.splitext(os.path.basename(path))[0]


def score_all(asof=None):
    """对所有公司计算当期综合得分。"""
    snap, period = load_snapshot(asof)
    companies = load_companies()
    out = []
    for c in companies:
        raw = snap.get("indicators", {}).get(c["id"])
        if raw is None:
            continue
        r = composite(raw)
        out.append({
            "id": c["id"], "name": c["name"], "camp": c.get("camp"),
            "sector": c.get("sector"), "listed": c.get("listed"),
            "valuation": c.get("valuation"), "arr": c.get("arr"),
            "score": r["score"], "ci_low": r["ci_low"], "ci_high": r["ci_high"],
            "confidence": r["confidence"], "dim_scores": r["dim_scores"],
        })
    out.sort(key=lambda x: x["score"], reverse=True)
    return {"period": period, "items": out}


def build_series():
    """跨期序列：每期各公司得分，用于趋势图。"""
    files = sorted([f for f in os.listdir(SNAP_DIR) if f.endswith(".json")])
    series = []
    for fn in files:
        period = os.path.splitext(fn)[0]
        r = score_all(asof=period)
        for it in r["items"]:
            series.append({"period": period, "id": it["id"], "name": it["name"],
                           "score": it["score"]})
    return series
