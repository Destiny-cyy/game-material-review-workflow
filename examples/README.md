# examples —— 示例数据（全部为编造，可安全外发）

> ⚠️ 本目录所有数字、游戏名、图片链接、人群分层、**日期**都是**编的假数据**，只用来让你在不接真实数据源的情况下，把脚本空跑一遍、确认「配置读得到、脚本能跑通、产物长这样」。
> 和任何真实项目、真实业务数据没有任何关系。
> 表里的 `2026-01` 这类年月只是为了让「按月分组」能跑出结果，**不代表任何真实投放档期**，正式使用时会被你的真实数据整批替换掉。

## 文件清单

| 文件 | 是什么 | 对应脚本 |
|---|---|---|
| `config.demo.json` | 一份「填好」的示例配置，指向本目录的假数据 | 所有脚本 |
| `master.sample.csv` | 投放明细主表（含复用：一张图被多条记录投） | `fetch_materials.py` 的产出形态 |
| `labels.sample.json` | 逐张看图打标的结果 | `label_merge.py` 的输入形态 |
| `tagged.sample.csv` | 打标回填后的明细（分析主输入） | `analyze.py` / `reuse_map.py` |
| `bench.json` | 大盘「游戏 × 月」聚合（假） | `benchmark.py` |
| `bench_materials.json` | 大盘「单条素材」明细（假） | `benchmark.py` |

## 三分钟空跑（不需要联网、不需要在线表格授权）

**从包根目录执行**（就是能看到 `README.md` 和 `examples/` 文件夹的那一层）：

```bash
# 1. 用示例配置跑分析（读假 tagged 数据）
python skills/ad-material-review/scripts/analyze.py \
  --config examples/config.demo.json \
  --csv examples/tagged.sample.csv \
  --out examples/out/analysis.json

# 2. 跑大盘双口径对比
python skills/ad-material-review/scripts/benchmark.py \
  --config examples/config.demo.json \
  --data-dir examples \
  --out examples/out/benchmark.json

# 3. 跑复用衰减明细
python skills/ad-material-review/scripts/reuse_map.py \
  --config examples/config.demo.json \
  --master examples/master.sample.csv \
  --tagged examples/tagged.sample.csv \
  --out examples/out/reuse_map.csv
```

跑完看 `examples/out/` 里的三个产物，就能确认整套流程的形状。

> **Windows 用户**：把命令里的 `\` 换行去掉、写成一行即可；或用 PowerShell 的反引号 `` ` `` 换行。
> 跑不通先检查两件事：① 是不是站在包根目录执行的；② Python 版本（需 3.8+）。
> 脚本会自动把 `scripts/` 加入模块搜索路径，所以不用额外配置 `PYTHONPATH`。

> `fetch_materials.py` / `write_smarttable.py` 依赖使用方配置的在线表格适配器，**不需要**在空跑里执行；
> 它们只在「接真实数据源」时才用，语法已通过校验。
