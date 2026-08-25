# 具身智能 / 物理AI 产业投资跟踪与分析体系 (embodied-ai-invest-system)

> 对应研究报告 **CHAPTER 07 · 具身智能与物理AI**。基于"六层栈估值框架"（算力>模型>大脑>整机>部件>应用）与"脑/手价值集中"产业判断，构建可复现、可扩展的开源分析仪表盘。

## EmbodiedCompete Index = 6.5 / 10

本体系用六维加权评分（量产确定性·商业化进度·技术壁垒·资本热度·供应链地位·政策/场景）对 25 家具身智能产业链标的进行梯队划分与动态排名，自动生成交互式 Dashboard（雷达图+Top12 横向排名+梯队切换表）与 JSON API。

## 目录结构

```
config/weights.json       六维权重配置
engine/scoring.py         评分引擎 + 梯队切分 + 六维均值
data/companies.json       25家标的池（海外整机/大脑 + 中国整机/灵巧手/部件/感知算力）
build_report.py           一键构建脚本（生成 REPORT.md + site/）
site/index.html           GitHub Pages 交互式 Dashboard
site/api/latest.json      最新排名与梯队 JSON
site/api/series.json      历史指数序列（便于做趋势图）
REPORT.md                 本赛道投资分析报告（人话版）
```

## 快速开始

```bash
python3 build_report.py       # 生成 REPORT.md + site/ 全部产物
python3 engine/scoring.py     # 仅输出指数与梯队统计
```

## 部署到 GitHub Pages

1. 新建仓库 `embodied-ai-invest-system`，推送本目录至 `main` 分支。
2. Settings → Pages → Source 选择 `gh-pages` (root)，首次手动运行 Actions 后每周自动重建。
3. 访问 `https://<your-org>.github.io/embodied-ai-invest-system/` 查看 Dashboard。

## 标的池覆盖（25家）

| 阵营 | 代表标的 |
|---|---|
| 海外整机/大脑 | 特斯拉 Optimus · Figure AI · Physical Intelligence · Skild AI · 英伟达 GR00T |
| 中国整机 | 宇树科技 · 智元机器人 · 优必选 · 越疆 · 银河通用 |
| 灵巧手 | 灵心巧手 · 舞肌科技 · 因时机器人 · 强脑科技 |
| 核心部件(卖铲人) | 绿的谐波 · 三花智控 · 拓普集团 · 兆威机电 · 鸣志电器 · 雷赛智能 |
| 感知/算力底座 | 地平线机器人 · 禾赛科技 · 速腾聚创 · 地瓜机器人 |
| 应用集成 | 极智嘉 |

## 免责声明

数据基线为公开信息近似整理（2026Q2 快照），指标原始值为人工近似评分，仅供趋势研究与学术探讨，**不构成任何投资建议**。市场有风险，投资需谨慎。

---
*内容由 AI 生成整理，不构成任何投资建议。*
