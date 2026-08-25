# -*- coding: utf-8 -*-
"""梯队划分 + 配置建议标签（AI生命科学定制）。"""
from engine.scoring import score_all

def tier_of(s):
    sc = s["score"]
    if sc >= 62: return "领跑"
    if sc >= 54: return "跟进"
    if sc >= 46: return "潜力"
    return "观察"

def config_tag(c):
    role = (c.get("role") or "").lower()
    track = (c.get("track") or "")
    # 卖铲人/平台型确定性最高
    if any(k in role for k in ["卖铲人", "平台", "saas", "超级甲方", "卖水人", "自动化机器人实验室", "临床ai"]):
        return "核心仓(卖铲人/平台)"
    # 脑机非侵入/微创已商业化或拟IPO
    if "非侵入" in track or "微创" in track:
        if any(k in role for k in ["卖铲人", "拟ipo", "消费"]):
            return "核心仓(脑机落地)"
    # 管线型高赔率
    if "管线" in role or "高通量" in role or "联邦" in role:
        return "管线期权仓(高赔率)"
    # 远期信仰
    if "信仰" in role or "资本密集" in role:
        return "信仰仓(远期)"
    return "路线/观察仓"

def analyze(companies):
    scored = score_all(companies)
    for s in scored:
        orig = next((x for x in companies if x.get("id") == s["id"]), {})
        s["tier"] = tier_of(s)
        s["config"] = config_tag(orig)
    return scored
