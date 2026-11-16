# ad-material-review · 技术 README

> **一句话**：一套「把投放素材的长相变成可计算字段，再跟曝光/点击拼起来做归因」的通用工作流，游戏、平台、标签体系、节点档期、对标对象、报告口径全部由配置驱动，换一款游戏只改配置文件。
>
> **本文面向**：要接手、迁移、二次开发这套流程的工程师，或需要精确知道「哪个脚本吃什么、吐什么」的技术型投放同学。
> **本文讲四件事**：作用 → 用法 → 工作流 → 项目架构。

---

## 0. 先看这份文档导航（本 skill 里四类文档别读混）

| 文件 | 写给谁 | 回答什么问题 | 什么时候读 |
|---|---|---|---|
| `README.md`（本文） | 接手/迁移/二开的人 | 作用、用法、工作流、**项目架构**、数据契约、扩展点 | 第一次接手、要改脚本或换游戏时 |
| `说明文档.md` | 业务同学、投放运营 | 大白话讲「这套东西解决什么问题、换游戏改哪里、坑在哪」 | 只想用、不想碰技术时 |
| `SKILL.md` | **Agent（AI）** | 执行规矩、硬性规则、七阶段动作、自检清单 | 让 AI 跑这套流程时必读 |
| `config/config.schema.md` | 配置的人 | 每个配置字段的含义、迁移检查清单 | 改 `config.json` 时 |

> 本文不重复 `说明文档.md` 的业务科普，也不重复 `SKILL.md` 的执行纪律；需要那部分请直接看对应文件。
> 包级总入口是包根目录 `README.md`，跨 skill 的迁移说明是《迁移到新游戏指南.md》。

---

## 1. 作用

### 1.1 它补的是哪一个缺口

投放后台给你的数据只有「曝光、点击、CTR、日期、人群、素材 ID」——**它不会告诉你这张图画的是什么**。
所以「哪种画风 CTR 高」「放福利有没有用」「老用户吃哪一套」这类问题，光看后台数字根本无法回答，因为「画风」「福利呈现」这些维度压根不在数据里。

这套工作流补的就是这一环：

```
素材图（非结构化） ──多模态看图──► 视觉标签（结构化）
                                      │
投放明细（曝光/点击/分层） ───────────┼──► 标签 × CTR 归因 ──► 结论 / 报告 / 下轮排期
                                      │
                              唯一图去重 + 复用衰减 + 大盘 Benchmark
```

一句话价值：**把「设计感觉」变成「可对比的数字」，让下一轮做素材有依据**。

### 1.2 能力清单

| 输入 | 产出 |
|---|---|
| 投放明细（只读） + 素材图片 | 唯一创意图片库、结构化打标明细（`tagged.csv`）、在线打标子表 |
| 打标明细 | 整体/月度/节点/用户分层/画风/画面元素/福利呈现/画风×福利 的曝光加权 CTR 归因 |
| 投放明细 | 素材复用衰减（第 N 次复用的效率是否倒挂） |
| 大盘聚合 + 大盘素材明细 | 游戏级与素材级**双口径** Benchmark（中位、排名、分位、别名合并） |
| 以上全部 | HTML 复盘报告、素材缺口测算、P0–P3 优先级与按周排期 |
| 打标明细 | 按标签批量重命名素材图（默认 dry-run） |

### 1.3 设计目标（也是判断改动是否合理的标准）

1. **配置是唯一事实源**：游戏名、平台名、子表名、字段名、标签体系、档期、对标游戏、图片域名、叙事策略全部只在 `config/` 里，脚本与方法论文档不写死任何具体值。
2. **换游戏不改脚本**：`source.mode` 与 `report.narrative` 两个开关吸收了原本两套流程的差异；标签体系可整包替换（`presets/`）。
3. **口径可审计**：CTR 一律曝光加权；每张交付物声明「唯一创意图数 vs 投放记录数」；每个结论带样本/曝光/CTR 三个数。
4. **脱敏可外发**：包内不含任何真实游戏名、平台名、真实业务数字、内部文档 ID、人名、内网链接；`examples/` 全是编造的假数据。
5. **无重量依赖**：脚本只用 Python 标准库，离线可空跑；在线表格能力是可选插件，不联网也能跑完分析主链。

### 1.4 边界（不做什么）

- 不负责**采集**投放数据（由在线表格/广告后台提供），只读不写原表。
- 不负责**生成**素材图，只评估已有素材、给出下轮方向。
- 不自动判断画面内容之外的因果（CTR 差异是相关性，不承诺因果）。
- `market_table` 模式下通常没有人群分层字段，做不了用户分析，需从广告后台补数据。

---

## 2. 快速开始

### 2.1 前置条件

- Python **3.8+**（仅标准库：`json` / `csv` / `os` / `urllib` / `argparse` / `collections`）。
- 命令行即可，**不需要安装任何第三方包**。
- 只有阶段 1 取数、阶段 4 写在线表格需要在线表格授权；分析主链完全离线。

### 2.2 三分钟空跑（不联网、不需要授权、全假数据）

**从包根目录执行**（能看到 `README.md` 和 `examples/` 的那一层）：

```bash
# 1) 多维度归因 + 复用衰减
python skills/ad-material-review/scripts/analyze.py \
  --config examples/config.demo.json \
  --csv examples/tagged.sample.csv \
  --out examples/out/analysis.json

# 2) 大盘双口径对比
python skills/ad-material-review/scripts/benchmark.py \
  --config examples/config.demo.json \
  --data-dir examples \
  --out examples/out/benchmark.json

# 3) 复用衰减明细
python skills/ad-material-review/scripts/reuse_map.py \
  --config examples/config.demo.json \
  --master examples/master.sample.csv \
  --tagged examples/tagged.sample.csv \
  --out examples/out/reuse_map.csv
```

跑完看 `examples/out/` 里三个产物即可确认「配置读得到、脚本跑得通、产物长这样」。
Windows 下把 `\` 换行去掉写成一行即可。脚本会自动把 `scripts/` 加入模块搜索路径，无需配 `PYTHONPATH`。

### 2.3 接真实数据的三步

```bash
cd skills/ad-material-review
cp config/config.example.json config/config.json     # ① 复制示例配置
# ② 编辑 config.json：按 config/config.schema.md 逐区块填写真实值
python scripts/fetch_materials.py --out-dir ./data    # ③ 取数，产出 data/master.csv 与唯一图
```

之后按第 4 节的流水线依次执行。改配置的完整清单见《迁移到新游戏指南.md》。

---

## 3. 用法

### 3.1 方式 A：作为 Agent Skill（主要用法）

把整个 `ad-material-review/` 目录放进 Agent 的 skills 目录，Agent 读 `SKILL.md` 后按七阶段推进。典型提示词：

```text
用 ad-material-review 做一次投放素材复盘：
- 目标：<游戏名> 在 <平台> <数据区间> 的投放素材
- 数据源：在线表格「<文档> → <明细子表>」（原表只读）
- 标签体系：套用 config/presets/preset.A.json，按实际画风微调
- 报告叙事：neutral（内部复盘用）
- 交付：HTML 报告 + 缺口测算 + 按周排期
```

触发词见 `SKILL.md` 的 frontmatter（素材复盘、素材打标、用户分层效率、复用衰减、大盘对比、缺口测算、素材图重命名等）。

### 3.2 方式 B：作为独立命令行脚本

每个脚本都能单独运行，公共参数由 `config_loader.add_config_arg()` 注入：

**`--config` 的查找顺序（四级，写在 `config_loader.load_config()` 里）**

```
① 命令行 --config 路径
② 环境变量 AD_REVIEW_CONFIG
③ 本包 config/config.json（正式）
④ 本包 config/config.example.json（示例，仅空跑演示）
```

> 显式指定（①②）但文件不存在时会**直接报错退出**，不会悄悄回退到示例配置；只有「没显式指定且正式 config.json 不存在」才回退并打印提示。这一点是刻意设计，避免「以为配置生效、其实用了假数据」。

**完整参数表**（默认值即脚本内实际值）

| 脚本 | 关键参数（默认值） | 输入 → 输出 | 联网 |
|---|---|---|---|
| `config_loader.py` | `--config`（由 `add_config_arg` 提供） | 配置 → dict | 否 |
| `fetch_materials.py` | `--out-dir`（=`output.data_dir`）、`--raw-json`、`--no-download` | 在线表 / JSON 快照 → `master.csv` + 唯一图 | 在线模式需要 |
| `label_merge.py` | `--labels-dir ./data`、`--pattern labels_b*.json`、`--master ./data/master.csv`、`--out ./data/tagged.csv` | 打标 JSON + master → `tagged.csv` | 否 |
| `write_smarttable.py` | `--csv ./data/tagged.csv`、`--batch 50` | `tagged.csv` → 在线打标子表 | 需要 |
| `analyze.py` | `--csv ./data/tagged.csv`、`--out ./data/analysis.json` | `tagged.csv` → `analysis.json` | 否 |
| `benchmark.py` | `--data-dir ./examples`、`--out ./data/benchmark.json` | `bench.json` + `bench_materials.json` → `benchmark.json` | 否 |
| `reuse_map.py` | `--master ./data/master.csv`、`--tagged`、`--out ./data/reuse_map.csv`、`--min-impression 0` | `master.csv`（+ 打标）→ `reuse_map.csv` | 否 |
| `rename_images.py` | `--map ./data/tagged.csv`、`--dir ./data/素材图`、`--apply`、`--out` | 打标 CSV + 图片目录 → 重命名 / 映射 CSV | 否 |

> `--batch` 务必保留分批：命令行过长会报错，在线表格单批写入有上限。
> `rename_images.py` 默认只预览，`--apply` 才真正改名。
> `fetch_materials.py --raw-json snapshot.json` 可完全离线从已导出快照生成 `master.csv`。

---

## 4. 工作流（七阶段 + 数据流）

### 4.1 七阶段总览

| 阶段 | 做什么 | 主执行者 | 脚本 | 输入 → 输出 |
|---|---|---|---|---|
| 1 摸底与取数 | 先 GROUP BY 看分布与月份覆盖，再拉明细；按图片链接去重下图 | Agent + 脚本 | `fetch_materials.py` | 在线表 → `master.csv` + 唯一图 |
| 2 建立/复用标签库 | 抽样看 8–10 张图校准；复用 `presets/` 或改 `taxonomy` | 人 + Agent | — | — → 定稿标签体系 |
| 3 逐张看图打标 | 唯一图分 4–5 批并行派子智能体多模态看图，产出 JSON；主会话抽查 4–6 张 | Agent | `label_merge.py` | `labels_b*.json` + `master.csv` → `tagged.csv` |
| 4 写入智能表格 | 新建打标子表、分批写、设列宽、回读校验 | 脚本 | `write_smarttable.py` | `tagged.csv` → 在线子表 |
| 5 效果分析 | 多维度曝光加权 CTR、复用衰减、大盘双口径 | 脚本 | `analyze.py` / `reuse_map.py` / `benchmark.py` | → 三个 JSON/CSV |
| 6 产出交付物 | 填 HTML 报告、可选在线文档、按叙事策略裁剪 | Agent | `assets/report_template.html` | → HTML 报告 |
| 7 缺口测算与排期 | 需求侧 vs 供给侧、三条假设、P0–P3 + 暂缓清单 | 人 + Agent | — | → 排期与优先级 |

### 4.2 数据流水线（真实文件流转）

```
  [在线表格 / 快照JSON]  ──只读──►  fetch_materials.py
                                      │ master.csv        记录级，一行 = 一次投放
                                      │ 素材图/<编号>.jpg  按 image_url 去重后的唯一创意图
                                      ▼
                        [多模态逐张看图，分批产出 JSON]
                                      │ labels_b1.json … labels_bN.json
                                      ▼
                        label_merge.py  ──►  tagged.csv
                        （图→记录回填 + 节点判定）        ★ 分析主输入
                                      │
        ┌─────────────────────┬──────────────────┼──────────────────┐
        ▼                     ▼                  ▼                  ▼
  write_smarttable.py     analyze.py      reuse_map.py       benchmark.py
  （在线打标子表）      analysis.json    reuse_map.csv      benchmark.json
                              │                                   │
                              └──────────────┬────────────────────┘
                                             ▼
                     assets/report_template.html → HTML 复盘报告
                     + 阶段7 缺口测算 / P0–P3 排期（人工）
```

> 关键设计：**一张图会被多条投放记录复用**。所以打标按「唯一图」做（省钱省时），分析按「投放记录」加权（不失真），复用衰减按「唯一图」聚合。三者口径不同，禁止混用同一个数。

### 4.3 五条必须守住的口径

| 口径 | 规则 | 落地位置 |
|---|---|---|
| 曝光加权 CTR | `CTR(组) = SUM(点击) / SUM(曝光) × 100%`，禁止对各行 CTR 取平均 | `analyze.py` / `references/analysis-playbook.md` |
| 唯一图 vs 记录 | 每张交付物声明「M 条记录 = N 张唯一图」 | `SKILL.md` 硬性规则 6 |
| 样本量门槛 | 低于 `thresholds.min_sample` 的组只给方向性结论并标注「样本不足」 | `config.thresholds` |
| 大盘双口径 | 游戏级（曝光加权）+ 素材级（单张中位）都要算，两者结论可能相反 | `benchmark.py` |
| 游戏名变体合并 | `benchmark.aliases` 收齐所有名字再算，否则会得出 CTR≈0 的假结果 | `benchmark.py` 的 `canon()` |

完整 12 条硬性规则见 `SKILL.md`；结论写法与脱敏对照见 `references/analysis-playbook.md`。

---

## 5. 项目架构

### 5.1 目录树

```
ad-material-review/
├── README.md                    技术向说明（本文）
├── SKILL.md                     Agent 执行规矩（frontmatter + 硬性规则 + 七阶段 + 自检）
├── 说明文档.md                  业务向大白话讲解（配流程图）
│
├── config/                     ★ 唯一事实源：所有游戏/平台专属信息只在这里
│   ├── config.example.json      示例配置（9 个顶层区块，全占位/假数据）
│   ├── config.schema.md         逐字段说明 + 迁移检查清单
│   └── presets/                 可整包替换的标签体系
│       ├── preset.A.json        示例预设A（暗黑幻想向，8 画风 / 10 元素）
│       └── preset.B.json        示例预设B（科幻射击向，5 画风 / 9 元素）
│
├── scripts/                    可独立运行的 Python 脚本（仅标准库）
│   ├── config_loader.py         ★ 公共底座，所有脚本都依赖它
│   ├── fetch_materials.py       阶段1 取数
│   ├── label_merge.py           阶段3 打标合并
│   ├── write_smarttable.py      阶段4 写在线表格
│   ├── analyze.py               阶段5 多维度归因
│   ├── benchmark.py             阶段5b 大盘双口径
│   ├── reuse_map.py             阶段5c 复用衰减明细
│   └── rename_images.py         辅助：按标签重命名素材图
│
├── references/                 方法论资产（与代码解耦，换游戏不用改）
│   ├── tag-taxonomy.md          标签体系怎么建/判定/扩展
│   ├── analysis-playbook.md     分析口径、结论写法、缺口测算
│   ├── user-analysis.md         用户分层 × 素材标签 × CTR 交叉（对应「用户研究/分析」）
│   ├── table-ops.md             在线表格/智能文档操作要点与已知坑
│   └── doc-sync.md              文档对齐与「去旧」五步
│
└── assets/
    └── report_template.html     HTML 复盘报告模板（纯占位符，无真实内容）
```

> `data/` 是运行时目录（`output.data_dir` 默认 `./data`），**不进包、不进版本库**，可随时重建。

### 5.2 分层视图

```
┌──────────────────────────────────────────────────────────────┐
│ 配置层  config/     唯一事实源，换游戏只动这一层                 │
│ config.json · config.example.json · config.schema.md · presets │
└────────────────────────────┬─────────────────────────────────┘
                             │ load_config() 四级查找 + preset 合并
┌────────────────────────────▼─────────────────────────────────┐
│ 底座层  scripts/config_loader.py                               │
│ load_config / F / T / node_fn / add_config_arg / url_of        │
└──────┬──────────────┬──────────────┬──────────────┬──────────┘
       │              │              │              │
┌──────▼─────┐ ┌──────▼──────┐ ┌─────▼──────┐ ┌─────▼──────────┐
│ 取数层      │ │ 打标层       │ │ 分析层      │ │ 产出层          │
│ fetch_      │ │ label_merge  │ │ analyze     │ │ write_smarttable│
│ materials   │ │ rename_images│ │ benchmark   │ │ report_template │
│             │ │              │ │ reuse_map   │ │                 │
└──────┬──────┘ └──────┬───────┘ └─────┬───────┘ └─────┬──────────┘
       │              │              │              │
┌──────▼──────────────▼──────────────▼──────────────▼──────────┐
│ 数据层  data/（运行时中间产物）                                │
│ master.csv → labels_b*.json → tagged.csv → *.json / *.csv      │
└───────────────────────────────────────────────────────────────┘
       ▲
       │ 方法论约束（不改代码，只约束「怎么判、怎么写」）
┌──────┴───────────────────────────────────────────────────────┐
│ 文档层  references/ · SKILL.md · 说明文档.md · README.md       │
└───────────────────────────────────────────────────────────────┘
```

**分层原则**：配置层决定「是什么游戏、什么字段、什么标签」；底座层把它翻译成脚本能用的函数；执行层只做机械动作；文档层约束判断标准。**任何具体值都不许穿过底座层漏进脚本或方法论文档**。

### 5.3 模块依赖（config_loader 是唯一公共底座）

| 脚本 | 从 `config_loader` 引入 | 用途 |
|---|---|---|
| `fetch_materials.py` | `load_config, F, add_config_arg, url_of` | 列名映射 + URL 字段归一（dict→string） |
| `label_merge.py` | `load_config, T, node_fn, add_config_arg` | 标签取值 + 节点判定（关键词优先，其次日期区间） |
| `analyze.py` | `load_config, T, add_config_arg` | 标签取值 + 样本门槛 |
| `benchmark.py` | `load_config, add_config_arg` | 目标/别名/对标/月份/门槛 |
| `reuse_map.py` | `load_config, add_config_arg` | 输出目录、复用分档 |
| `rename_images.py` | `load_config, add_config_arg` | 元素分隔符、文件名清洗 |
| `write_smarttable.py` | `load_config, T, add_config_arg` | 建表字段与选项从 taxonomy 生成 |

底座提供的 6 个接口：

```text
load_config(path=None)  读配置（四级查找 + 可选 preset 合并覆盖 taxonomy/nodes）
F(cfg)                  返回「内部列名 → 源表真实列名」映射
T(cfg)                  返回标签体系 taxonomy
node_fn(cfg)             构造节点判定函数：关键词命中 > 日期区间 > default
add_config_arg(parser)  给每个脚本统一注入 --config 参数
url_of(v)                在线表格的 URL 字段可能是 dict，统一取 url/text 字符串
```

**preset 覆盖机制**：在 `config.json` 里写 `"preset": "preset.A.json"`，`load_config()` 会把该预设的 `taxonomy` / `nodes` 合并进配置（预设字段覆盖同名字段）。这就是「同一套脚本、两套标签体系」的实现方式，不需要改一行代码。

### 5.4 配置驱动的 9 个区块 + 2 个开关

`config.example.json` 顶层区块：

| 区块 | 管什么 | 被谁读 |
|---|---|---|
| `project` | 游戏名/代号/品类/平台/渠道/数据区间/重点月份/语言 | 报告标题、口径声明 |
| `source` | 取数方式、文档 ID、子表名、新建打标子表、只读标志 | `fetch_materials.py`、`write_smarttable.py` |
| `fields` | **源表真实列名 → 内部统一列名**的对照（最容易踩坑） | 所有读 CSV 的脚本 |
| `taxonomy` | 画风(单选) / 画面元素(多选) / 福利呈现(单选) / 人群分层 / 置信度 / 元素上限与分隔符 | 打标、建表、分析 |
| `nodes` | 节点判定：关键词、日期区间、兜底值 | `node_fn()` → `label_merge.py` |
| `benchmark` | 目标游戏、名字变体 aliases、对标游戏、月份、参评曝光门槛 | `benchmark.py` |
| `thresholds` | 最小样本、TOP 素材门槛、复用分档 | `analyze.py`、`reuse_map.py` |
| `output` | 中间产物目录、图片目录、CDN 域名、Referer、链接口径 | 全部脚本 |
| `report` | 叙事策略与展示开关 | 阶段 6 报告裁剪 |

两个吸收「原本两套流程差异」的开关：

| 开关 | 取值 | 差异 |
|---|---|---|
| `source.mode` | `own_ledger` | 自有投放台账，带人群分层/广告位字段 → **可做用户分层分析** |
| | `market_table` | 平台大盘表，按游戏名（含 aliases）过滤目标游戏 → 通常无分层字段 |
| `report.narrative` | `neutral` | 客观全量展示 |
| | `positive_only` | 只写优势与环比进步；排名/分位/垫底**仍要算出留档**，只是不进报告，交付时口头告知业务方本人 |
| | `full` | 全量含排名 |

> 这是把两套同源 skill 合并成一套的关键抽象：**流程差异不复制代码，只落到配置开关**。

### 5.5 数据契约（中间文件的真实字段）

| 文件 | 粒度 | 字段 |
|---|---|---|
| `master.csv` | 投放记录（一行一次投放） | `rowid, material_id, date, segment, position, title, desc, image_url, video_url, impressions, clicks` |
| `labels_b*.json` | 唯一创意图（数组） | 每条 `{img, style, elements[], benefit, desc, conf}`，`img` 对应该图**首次出现**的 `rowid` |
| `tagged.csv` | 投放记录（已回填标签） | `material_id, date, segment, position, node, style, elements, benefit, desc_visual, confidence, impressions, clicks, image_url`；`elements` 用 `element_separator` 分隔 |
| `bench.json` | 游戏 × 月 | `{g, m, imp, clk}` |
| `bench_materials.json` | 大盘单条素材 | `{g, imp, clk}` |
| `analysis.json` | 分析结果 | 顶层 8 个键：`整体月度 / 节点 / 画风 / 福利呈现 / 用户分层 / 画面元素（多选包含口径，组间重叠）/ 画风x福利 / 复用衰减` |

> 所有 CSV 用 `utf-8-sig` 读写（带 BOM，Excel 直接打开不乱码）。JSON 用 `ensure_ascii=False`。
> `label_merge.py` 回填时**必须保留同链接首次出现的 rowid**，否则大面积回填为空——这是实现里最容易踩的坑。

### 5.6 扩展点（要改东西时改哪里）

| 想改什么 | 改哪里 | 要不要动脚本 |
|---|---|---|
| 换游戏 / 换平台 / 换数据区间 | `config.project` | 不用 |
| 源表列名变了 | `config.fields` | 不用 |
| 换一整套画风/元素/福利标签 | `config.taxonomy` 或 `presets/` | 不用 |
| 加一个运营节点 / 改档期日期 | `config.nodes` | 不用 |
| 换对标游戏、加游戏名变体 | `config.benchmark` | 不用 |
| 调整样本门槛 / 复用分档 | `config.thresholds` | 不用 |
| 改报告能不能写排名 | `config.report` | 不用 |
| **加一个全新分析维度** | `analyze.py` 里加一个 `agg()` 调用 + `analysis.json` 键 | 要 |
| **加一种交付物** | `assets/` 加模板 + 阶段 6 动作 | 要（可能） |
| **换在线表格后端** | `write_smarttable.py` / `fetch_materials.py` 的 `call()` | 要 |

判据很简单：**凡是「换一款游戏就会变」的东西，都应该在 `config/`；凡是「换游戏也不变」的东西，才留在脚本里。**

---

## 6. 迁移到新游戏（简要）

1. `cp config/config.example.json config/config.json`
2. 按 `config/config.schema.md` 的「迁移检查清单」逐区块填真实值，重点：`source.mode` 选对、`fields` 与源表列名逐一核对、`benchmark.aliases` 收齐所有名字变体、`output.cdn_base` 换成真实图片域名、`nodes` 档期日期向业务确认。
3. 跑一次 `examples/` 空跑或 `--config` 指向新配置，确认脚本读得到配置。
4. 首次执行务必抽样看 8–10 张不同时期的图，校准标签体系。

一步步操作见包根目录《迁移到新游戏指南.md》。

---

## 7. 技术向避坑清单

| 类别 | 坑 | 对策 |
|---|---|---|
| 配置 | 显式 `--config` 路径写错，却以为配置生效 | `load_config()` 对显式路径不存在直接报错退出 |
| 配置 | 档期日期是推断值 | 每次复盘前向业务确认，只改 `nodes` |
| 数据 | 同图多条记录，回填大面积为空 | `label_merge.py` 保留首次出现的 `rowid` |
| 数据 | 把「唯一图数」当「记录数」写进口径 | 每张交付物声明两个数 |
| 数据 | 游戏名变体没合并 → CTR≈0 | `benchmark.aliases` + `canon()` |
| 统计 | 对各行 CTR 取简单平均 | 一律 `SUM(点击)/SUM(曝光)` |
| 统计 | 小样本刷榜 | `benchmark` 曝光门槛 + `thresholds.min_sample` |
| 看图 | 会话级图片缓存让重复读图返回 unchanged | 复制文件并在 JPEG 头插 COM 段绕过（见 `references/table-ops.md`） |
| 在线表格 | 命令行过长、单批写入超限 | `write_smarttable.py --batch` 分批；`replace` 后旧 block_id 会失效 |
| 产物 | 报告里出现本地路径 / 内网链接 | `output.link_policy = cdn_only`，对外只放 CDN 网址 |
| 文档 | 口径升级后「新增一节 + 保留旧节」 | 按 `references/doc-sync.md` 五步去旧 |

完整版见包根目录《分享包文档/避坑指南.md》。

---

## 8. 自检 / 验收

改动后建议按这个顺序验一遍：

```bash
# 1) 语法
python -m py_compile skills/ad-material-review/scripts/*.py

# 2) 配置可解析
python -c "import json; json.load(open('skills/ad-material-review/config/config.example.json',encoding='utf-8'))"

# 3) 三条空跑（见 2.2 节命令）
# 4) 敏感词扫描：全文不得出现真实游戏名/平台名/真实业务数字/内部 ID/人名/内网链接/本地绝对路径
# 5) 报告模板：只含 {{占位符}}，无真实内容
```

交付前对照 `SKILL.md` 末尾的「交付前自检清单」逐条打勾。

---

## 9. FAQ

**Q：不联网能用吗？**
A：分析主链（`analyze` / `benchmark` / `reuse_map` / `label_merge` / `rename_images`）完全离线，用 `examples/` 假数据即可空跑。只有取数和写在线表格需要在线表格授权；取数也支持 `--raw-json` 从快照离线生成 `master.csv`。

**Q：为什么有两套 preset，实际用哪套？**
A：它们只是演示「同一套流程能配不同标签体系」的样例，都不是生产配置。按你的游戏实际画风改 `config.taxonomy`，或复制一份 preset 再改，在 `config.json` 里用 `"preset"` 指向它。

**Q：`positive_only` 是不是隐瞒数据？**
A：不是。扎心数据（排名、分位、垫底、与头部差距）**仍要全部算出并内部留档**，只是不写进给更上层看的报告，交付时口头/私信告知业务方本人。这叫「不隐瞒，但不写进给更上层看的报告」。

**Q：想加一个分析维度要动几处？**
A：最小改动是 `analyze.py` 里加一次 `agg()` 并向 `analysis.json` 写一个新键；若新维度需要新标签，先在 `config.taxonomy` 加取值。方法论文档同步补口径说明即可，不用改其他脚本。

**Q：原表会被改坏吗？**
A：不会。`source.readonly = true` 是硬约束，打标结果只写进 `source.tag_sheet` 指定的**新建子表**。

---

> 本 skill 属于《游戏素材复盘工作流 · 脱敏通用版》分享包。包内业务闭环：
> `retrospective`（怎么复盘整理）→ `channel-resource-table`（向前看：这次收什么素材）→ 投放 → `ad-material-review`（向后看：做过的哪类好）→ 下一轮素材。
