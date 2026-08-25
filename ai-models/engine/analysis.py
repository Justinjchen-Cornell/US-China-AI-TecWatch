# -*- coding: utf-8 -*-
"""
AI 大模型生态投资体系 · 分析引擎
====================================
将 scoring/data 的输出转化为可阅读的投资分析结论：
- 梯队划分（领跑/跟进/潜力/观察）
- 维度雷达数据
- 配置含义（确定性核心 / 高弹性期权 / 主题卫星）
"""
from engine.data import score_all, load_companies


def tier(score):
    if score >= 62: return "领跑梯队"
    if score >= 54: return "跟进梯队"
    if score >= 46: return "潜力梯队"
    return "观察梯队"


def analyze():
    res = score_all()
    items = res["items"]
    for it in items:
        it["tier"] = tier(it["score"])
    tiers = {"领跑梯队": [], "跟进梯队": [], "潜力梯队": [], "观察梯队": []}
    for it in items:
        tiers[it["tier"]].append(it)
    # 维度平均（仅已评分公司）
    dim_avg = {}
    for d in ["model_capability","commercialization","open_source",
              "compute_efficiency","embodiment"]:
        vals = [it["dim_scores"][d] for it in items if it["dim_scores"].get(d) is not None]
        dim_avg[d] = round(sum(vals)/len(vals)*100, 1) if vals else None
    # 配置建议
    core = sorted([i for i in items if i["listed"]],
                  key=lambda x: x["score"], reverse=True)[:5]
    option_ = sorted([i for i in items if not i["listed"]],
                     key=lambda x: x["score"], reverse=True)[:4]
    return {
        "period": res["period"],
        "tiers": tiers,
        "items": items,
        "dim_avg": dim_avg,
        "core": core,
        "option": option_,
    }
