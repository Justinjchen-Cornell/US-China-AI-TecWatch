# -*- coding: utf-8 -*-
"""
AI 大模型生态投资体系 · 指标体系定义
====================================
维度（Dimension）与指标（Indicator）的单一来源（Single Source of Truth）。
- 权重与数据完全分离，可自由调整。
- direction: 'higher_better' = 值越大对中国/标的越有利；'lower_better' 反之。
- 归一化采用线性映射至 [0,1]，再参与维度几何平均 + 全局加权。
"""

DIMENSIONS = [
    "model_capability",   # 模型能力（通用/多模态/长文本/Agent）
    "commercialization",  # 商业化兑现（ARR/盈利/客户）
    "open_source",        # 开源与生态（非对称武器）
    "compute_efficiency", # 算力与成本效率（低成本推理/国产化）
    "embodiment",         # 具身智能 / 物理 AI（前瞻性）
]

# 各维度权重（可调整，运行时归一化为和为1）
DIMENSION_WEIGHTS = {
    "model_capability":   0.25,
    "commercialization":  0.25,
    "open_source":        0.15,
    "compute_efficiency": 0.20,
    "embodiment":         0.15,
}

INDICATORS = [
    # ---- 模型能力 ----
    {"id": "mmlu_score",       "dim": "model_capability",  "name": "通用知识 MMLU 类基准", "direction": "higher_better", "weight_in_dim": 0.30, "source_reliability": 0.85},
    {"id": "long_context",     "dim": "model_capability",  "name": "长文本上下文能力",     "direction": "higher_better", "weight_in_dim": 0.25, "source_reliability": 0.80},
    {"id": "multimodal",       "dim": "model_capability",  "name": "多模态（图/视频/3D）", "direction": "higher_better", "weight_in_dim": 0.25, "source_reliability": 0.75},
    {"id": "agent_capability", "dim": "model_capability",  "name": "Agent/工具使用能力",  "direction": "higher_better", "weight_in_dim": 0.20, "source_reliability": 0.70},
    # ---- 商业化兑现 ----
    {"id": "arr",              "dim": "commercialization", "name": "ARR 年度经常性收入",   "direction": "higher_better", "weight_in_dim": 0.45, "source_reliability": 0.80},
    {"id": "profitability",    "dim": "commercialization", "name": "盈利能力（毛利率/净利）","direction": "higher_better", "weight_in_dim": 0.35, "weight_note": "亏损取低值", "source_reliability": 0.85},
    {"id": "p_arr_multiple",   "dim": "commercialization", "name": "P/ARR 估值倍数",      "direction": "lower_better",  "weight_in_dim": 0.20, "source_reliability": 0.70},
    # ---- 开源与生态 ----
    {"id": "open_source_flag",  "dim": "open_source",       "name": "开源基座（是=1/否=0）","direction": "higher_better", "weight_in_dim": 0.55, "source_reliability": 0.90},
    {"id": "open_rank_share",  "dim": "open_source",       "name": "开源榜单/全球调用份额", "direction": "higher_better", "weight_in_dim": 0.45, "source_reliability": 0.70},
    # ---- 算力与成本效率 ----
    {"id": "inference_cost",    "dim": "compute_efficiency","name": "每百万 token 推理成本", "direction": "lower_better",  "weight_in_dim": 0.55, "source_reliability": 0.75},
    {"id": "compute_self_supply","dim": "compute_efficiency","name": "算力自给/国产化率",   "direction": "higher_better", "weight_in_dim": 0.45, "source_reliability": 0.65},
    # ---- 具身智能/物理AI ----
    {"id": "embodiment_progress","dim": "embodiment",       "name": "具身/物理AI进展",      "direction": "higher_better", "weight_in_dim": 0.60, "source_reliability": 0.55},
    {"id": "robotics_data",     "dim": "embodiment",       "name": "机器人真实数据闭环",   "direction": "higher_better", "weight_in_dim": 0.40, "source_reliability": 0.50},
]

# 归一化参考区间（min_raw, max_raw）-> 线性映射到 [0,1]
NORMALIZATION_BOUNDS = {
    # model_capability
    "mmlu_score":       (50.0, 90.0),
    "long_context":      (0.0, 200.0),    # 万 token 量级
    "multimodal":        (0.0, 1.0),      # 0=无/1=强
    "agent_capability":  (0.0, 1.0),
    # commercialization
    "arr":               (0.0, 50.0),      # 十亿美元
    "profitability":     (-1.0, 0.5),      # 亏损率(-1) -> 健康盈利(0.5)
    "p_arr_multiple":    (10.0, 300.0),    # 倍数越低越好
    # open_source
    "open_source_flag":  (0.0, 1.0),
    "open_rank_share":   (0.0, 0.5),       # 全球调用份额
    # compute_efficiency
    "inference_cost":    (0.1, 10.0),      # 美元/百万token（越高越贵）
    "compute_self_supply":(0.0, 1.0),
    # embodiment
    "embodiment_progress":(0.0, 1.0),
    "robotics_data":     (0.0, 1.0),
}
