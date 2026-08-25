#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
intel_html.py —— 行业研判区块统一渲染器
输入: industry_intelligence.json 的 dict
输出: 完整研判区块 HTML（verdict + 核心判断 + 技术路线 + 价值链 + 跟踪信号 + 拐点 + 底稿链接）
所有行业子站共用, 保证展示口径一致。
"""
import html as _html

def render(intel, accent="#38bdf8"):
    def esc(s):
        return _html.escape(str(s or ""))
    v = intel.get("verdict", {})
    core = intel.get("core_judgment", "")
    routes = intel.get("technology_routes", [])
    vc = intel.get("value_chain", [])
    signals = intel.get("track_signals", [])
    inf = intel.get("inflections_6_18m", [])
    ref = intel.get("methodology_ref", "")

    h = "<div class='card' style='border-left:4px solid " + accent + ";margin-bottom:18px'>"
    h += "<div style='font-size:12px;color:#7a8699;letter-spacing:.5px'>行业研判 · 非评分 · 作者观点</div>"
    h += "<h2 style='font-size:17px;margin:8px 0 6px'>" + esc(v.get("phase", "")) + "</h2>"
    if core:
        h += "<div style='font-size:13px;line-height:1.7;margin:6px 0 10px;color:#334155'><b>核心判断：</b>" + esc(core) + "</div>"
    h += "<table style='font-size:13px'><tbody>"
    h += "<tr><th style='text-align:left;width:130px'>中国位置</th><td>" + esc(v.get("china_position", "")) + "</td></tr>"
    h += "<tr><th style='text-align:left'>关键拐点</th><td>" + esc(v.get("key_inflection", "")) + "</td></tr>"
    h += "<tr><th style='text-align:left'>投资主题</th><td>" + esc(v.get("investment_theme", "")) + "</td></tr>"
    h += "</tbody></table>"

    if routes:
        h += "<div style='font-size:13px;font-weight:600;margin:12px 0 6px'>技术路线全景</div>"
        h += "<ul style='margin:0;padding-left:18px;font-size:12.5px;color:#334155'>"
        for r in routes:
            line = "<b>" + esc(r.get("name", "")) + "</b>（" + esc(r.get("maturity", "")) + "）"
            if r.get("cn_players"):
                line += " · 中: " + esc("、".join(r["cn_players"]))
            if r.get("us_players"):
                line += " / 美: " + esc("、".join(r["us_players"]))
            if r.get("convergence_signal"):
                line += " · 信号: " + esc(r["convergence_signal"])
            h += "<li>" + line + "</li>"
        h += "</ul>"

    if vc:
        h += "<div style='font-size:13px;font-weight:600;margin:12px 0 6px'>价值链判断</div>"
        h += "<ul style='margin:0;padding-left:18px;font-size:12.5px;color:#334155'>"
        for seg in vc:
            h += "<li><b>" + esc(seg.get("segment", "")) + "</b>（价值集中度 " + esc(seg.get("value_concentration", "")) + "）：" + esc(seg.get("logic", "")) + "</li>"
        h += "</ul>"

    if signals:
        h += "<div style='font-size:13px;font-weight:600;margin:12px 0 6px'>跟踪信号（定期验证）</div>"
        h += "<ul style='margin:0;padding-left:18px;font-size:12.5px;color:#334155'>"
        for s in signals:
            h += "<li>" + esc(s) + "</li>"
        h += "</ul>"

    if inf:
        h += "<div style='font-size:13px;font-weight:600;margin:12px 0 6px'>未来 6-18 个月拐点</div>"
        h += "<ul style='margin:0;padding-left:18px;font-size:12.5px;color:#334155'>"
        for x in inf:
            h += "<li><b>" + esc(x.get("event", "")) + "</b>（概率 " + esc(x.get("probability", "")) + "）：" + esc(x.get("impact", "")) + "</li>"
        h += "</ul>"

    if ref:
        h += "<div style='font-size:12px;margin-top:10px'><a href='https://github.com/Justinjchen-Cornell/US-China-AI-TecWatch/blob/main/docs/methodology.md" + esc(ref) + "' style='color:#4f8cff;text-decoration:none'>📘 方法论底稿" + esc(ref) + " →</a></div>"
    h += "</div>"
    return h
