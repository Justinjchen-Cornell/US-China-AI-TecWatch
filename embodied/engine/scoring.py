# -*- coding: utf-8 -*-
"""具身智能六维评分引擎（薄壳，逻辑委托给 _scorelib）。"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from _scorelib import score_all, dim_means, tier_split
if __name__ == "__main__":
    comps = score_all()
    print("EmbodiedCompete Index =", round(sum(c["score"] for c in comps)/len(comps), 1))
    for t, arr in tier_split(comps).items():
        print(f"[%s] %d" % (t, len(arr)))
