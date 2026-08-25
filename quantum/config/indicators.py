# -*- coding: utf-8 -*-
"""量子计算产业投资分析 —— 六维指标体系与权重配置。

权重与数据完全分离：调整权重只需改本文件，重跑 build_report.py 即生效。
行业逻辑（CHAPTER 02）：量子比特是"容易摔倒的小朋友"，需抱团成逻辑比特；
四条硬件路线（超导/离子阱/中性原子/光量子）均未到终点，故投资主线为
"先投激光器/制冷机/测控等卖铲人部件商，整机厂(Quantinuum/IonQ/本源等)只作期权"。

维度含义（数值越高代表该维度越强/越有利）：
  1. 技术成熟度 tech_maturity   : 物理比特数/逻辑比特进展/纠错水平
  2. 商业化进度 commercial      : 营收/订单/客户落地/上市进展
  3. 资本热度   capital         : 估值/融资轮次/头部机构背书
  4. 路线确定性 route_certainty : 技术路线主流度/工程可扩展性
  5. 供应链地位 supply_chain    : 部件/测控/仪器等卖铲人属性(确定性)
  6. 政策战略   policy_strategic: 国产替代/量子安全/国家战略价值
"""

DIMENSIONS = [
    "tech_maturity",
    "commercial",
    "capital",
    "route_certainty",
    "supply_chain",
    "policy_strategic",
]

WEIGHTS = {
    "tech_maturity":   1.15,  # 技术壁垒最高权重
    "commercial":      1.10,  # 商业化兑现次之(本章强调"证明能卖出去")
    "capital":         0.85,
    "route_certainty": 1.00,
    "supply_chain":    1.05,  # 卖铲人确定性(行业核心逻辑)
    "policy_strategic": 0.85,  # 中国视角/国家战略加分
}

# 归一化方向：仅用于展示，不影响得分计算
DIRECTION = {
    "tech_maturity":   "higher_better",
    "commercial":      "higher_better",
    "capital":         "higher_better",
    "route_certainty": "higher_better",
    "supply_chain":    "higher_better",
    "policy_strategic": "cn_benefit",
}

DIM_LABEL = {
    "tech_maturity":  "技术成熟度",
    "commercial":     "商业化进度",
    "capital":        "资本热度",
    "route_certainty": "路线确定性",
    "supply_chain":   "供应链(卖铲人)地位",
    "policy_strategic": "政策/战略价值",
}
