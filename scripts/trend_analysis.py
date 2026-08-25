#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
trend_analysis.py —— 行业趋势解读（趋势方向 / 动量 / 驱动归因 / 观察清单）

定位：指数只是手段，趋势与方向才是目的。本模块把"3 点时间序列"翻译成
可读的行业趋势判断，并归因到具体指标（回答"指数为什么变"）。

输出 trend 字段（随 latest.json 发布）:
  direction  : up / down / flat            —— 近两年方向（首尾对比）
  delta      : 首尾指数差
  momentum   : accelerating / steady / slowing —— 动量（两段斜率对比）
  vs_parity  : 相对 50 均势线的状态
  drivers    : 指标级归因 [{id,name,delta_norm}]（哪个指标变化最大）
  watch      : 观察清单（人工维护，来自 industry_indicators.json 的 watch 字段）
"""
import json

def analyze(indicators_now, indicators_first, series, watch=None, eps=1e-6):
    """indicators_now/indicators_first: 指标定义列表(含 norm 计算所需的原始值/ref)
       series: [{"as_of","index"}...] 至少 2 点"""
    if len(series) < 2:
        return {"direction": "flat", "delta": 0.0, "momentum": "steady",
                "vs_parity": "insufficient_data", "drivers": [], "watch": watch or []}
    first, last = series[0]["index"], series[-1]["index"]
    delta = round(last - first, 1)
    if delta > 0.5:
        direction = "up"
    elif delta < -0.5:
        direction = "down"
    else:
        direction = "flat"

    # 动量: 两段斜率
    if len(series) >= 3:
        seg1 = series[1]["index"] - series[0]["index"]
        seg2 = series[2]["index"] - series[1]["index"]
        if seg2 > seg1 + 0.5:
            momentum = "accelerating"
        elif seg2 < seg1 - 0.5:
            momentum = "slowing"
        else:
            momentum = "steady"
    else:
        momentum = "steady"

    # 相对均势线
    if first < 50 <= last:
        vs_parity = "crossed_above"
    elif first > 50 >= last:
        vs_parity = "crossed_below"
    elif last >= 50:
        vs_parity = "leading" if last >= first else "eroding"
    else:
        vs_parity = "trailing" if last <= first else "closing"

    # 驱动归因: 每指标 norm(当前) - norm(历史首期)
    def _norm(ind):
        v = float(ind.get("value"))
        lo, hi = float(ind["ref_min"]), float(ind["ref_max"])
        if ind.get("log_scale"):
            import math
            s = math.log(1.0 + max(0.0, v - lo)) / math.log(1.0 + (hi - lo))
        elif hi != lo:
            s = (v - lo) / (hi - lo)
        else:
            s = 0.5
        s = max(0.0, min(1.0, s))
        if int(ind.get("direction", 1)) == -1:
            s = 1.0 - s
        return s

    drivers = []
    for i_now, i_first in zip(indicators_now, indicators_first):
        if i_now.get("value") is None or i_first.get("value") is None:
            continue
        d = round(_norm(i_now) - _norm(i_first), 4)
        drivers.append({"id": i_now["id"], "name": i_now["name"], "delta_norm": d})
    drivers.sort(key=lambda x: -abs(x["delta_norm"]))

    return {"direction": direction, "delta": delta, "momentum": momentum,
            "vs_parity": vs_parity, "drivers": drivers[:5], "watch": watch or []}
