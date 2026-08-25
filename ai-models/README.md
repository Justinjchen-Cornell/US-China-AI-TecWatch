# AI 大模型生态投资体系 (ai-model-invest-system)

将一份「AI 大模型产业分析」沉淀为**可跟踪、可复算、可部署**的投资研究体系：
数据(JSON) → 指标归一化 → 五维加权综合评分 → 梯队/配置建议 → 单页 Dashboard + JSON API。

## 体系构成
- `config/indicators.py`：五维指标体系（模型能力/商业化/开源/算力效率/具身智能）与归一化区间——**唯一需要调整权重的地方**。
- `engine/scoring.py`：综合评分引擎（归一化 → 维度几何平均 → 全局加权 → sigmoid 映射 → 蒙特卡洛 ±1σ）。
- `engine/data.py`：公司基本面 + 各期指标快照加载。
- `engine/analysis.py`：梯队划分 + 配置含义（确定性核心 / 高弹性期权）。
- `build_report.py`：生成 `site/api/latest.json`、`site/api/series.json`、`site/index.html`。
- `data/companies.json` + `data/snapshots/2026Q2.json`：示例公司池与一期指标快照（基于公开信息近似整理）。

## 本地使用
```bash
pip install -e .
python build_report.py
# 打开 site/index.html 查看 Dashboard；site/api/latest.json 可供外部调用/复算
```
新增一期数据：在 `data/snapshots/` 新增 `YYYYQN.json`（同结构），重跑即更新趋势序列。

## 发布到 GitHub Pages
1. 新建仓库（如 `ai-model-invest-system`），推送全部文件至 `main` 分支；
2. **Settings → Pages → Source 选 `gh-pages` 分支 / `(root)`**；
3. 首次手动运行一次 Actions（`workflow_dispatch`），之后每周自动重建；
4. 站点地址：`https://<用户名>.github.io/ai-model-invest-system/`。

## 评分方法（透明可复算）
1. 每指标按方向线性归一化到 [0,1]；
2. 维度内按权重做 Laplace 平滑几何平均；
3. 五维按 `DIMENSION_WEIGHTS` 加权合成后 sigmoid 映射到 (0,100)；
4. 基于 `source_reliability` 做蒙特卡洛（N=2000）得 ±1σ 区间。

> 数据基线来自公开研究与报告，指标原始值为近似整理，仅供趋势研究与学术探讨，**不构成任何投资建议**。
