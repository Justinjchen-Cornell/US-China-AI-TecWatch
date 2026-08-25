# -*- coding: utf-8 -*-
"""具身智能六维评分库（独立模块，供 scoring.py 与构建脚本共用）。"""
import json, os
_HERE = os.path.dirname(__file__)
_ROOT = os.path.dirname(_HERE)

def load_companies():
    return json.load(open(os.path.join(_ROOT, "data", "companies.json"), encoding="utf-8"))["companies"]

def load_weights():
    return json.load(open(os.path.join(_ROOT, "config", "weights.json"), encoding="utf-8"))

def wd():
    return {d["key"]: d["w"] for d in load_weights()["dims"]}

def score_one(c, wdict=None):
    if wdict is None:
        wdict = wd()
    return round(c["mass"]*wdict["mass"]+c["comm"]*wdict["comm"]+c["tech"]*wdict["tech"]
                +c["cap"]*wdict["cap"]+c["supply"]*wdict["supply"]+c["policy"]*wdict["policy"], 1)

def score_all(comps=None):
    if comps is None:
        comps = load_companies()
    w = wd()
    for c in comps:
        c["score"] = score_one(c, w)
    return comps

def dim_means(comps):
    return {d: round(sum(c[d] for c in comps)/len(comps),2) for d in ["mass","comm","tech","cap","supply","policy"]}

def tier_split(comps):
    return {"lead":[c for c in comps if c["score"]>=7.5],
            "follow":[c for c in comps if 6.5<=c["score"]<7.5],
            "pot":[c for c in comps if c["score"]<6.5]}
