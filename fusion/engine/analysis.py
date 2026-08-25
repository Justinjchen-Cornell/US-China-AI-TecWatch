# -*- coding: utf-8 -*-
"""梯队划分 + 配置建议标签。"""
from engine.scoring import score_all

def tier_of(s):
    sc = s["score"]
    if sc >= 70: return "领跑"
    if sc >= 58: return "跟进"
    if sc >= 46: return "潜力"
    return "观察"

def config_tag(c):
    role = (c.get("role") or "").lower()
    if "supply" in role or "磁体" in role or "材料" in role or "卖铲" in role:
        return "核心仓(卖铲人)"
    if "整机" in role or "reactor" in role:
        return "整机期权仓"
    return "路线/观察仓"

def analyze(companies):
    scored = score_all(companies)
    for s in scored:
        orig = next((x for x in companies if x.get("id") == s["id"]), {})
        s["tier"] = tier_of(s)
        s["config"] = config_tag(orig)
        s["market"] = orig.get("market", "")
    return scored
