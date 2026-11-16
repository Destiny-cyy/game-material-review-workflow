# 游戏素材复盘工作流

> **版本 v1.1.0（分发就绪版）** · 变更记录见 `CHANGELOG.md` · 使用许可见 `LICENSE`
>
这套工作流用于素材打标、效果归因、用户分层、大盘对比、复用衰减和素材缺口测算。游戏、平台、标签和报告口径由配置文件提供，迁移项目时不需要改分析脚本。

仓库不含真实游戏、平台、业务数据、内部文档 ID 或人员信息。所有示例数据都是合成值；公开分发前仍应按第十一节重新检查配置和输出文件。

> **场景模板**：仓库内的游戏、平台、渠道、对标对象与指标均为可配置占位符或合成演示值。先在 `config.example.json` 的副本中填写 `{{GAME_NAME}}`、`{{PLATFORM_NAME}}` 等字段，再接入获准的数据源；示例不代表任何真实项目。

## 报告预览

[打开完整 HTML 场景报告](examples/material-review-report.html)

![素材复盘场景报告](docs/images/material-review-report.png)

页面展示一份可配置的报告结构，包括素材指标、创意方向、人群交叉和行动队列。数值为合成演示值。

---

## 一、适用问题

这套工作流适合处理以下问题：

- 哪种画风的素材更吸引人？画面上放不放福利、怎么放有没有用？ → **素材复盘**
- 老用户 / 新用户分别吃哪一套？下轮资源怎么分？ → **用户分层分析**
- 一张图反复投会不会越投越没效果？跟平台上别的游戏比算什么水平？ → **大盘对比 / 复用衰减**
- 下个月要新做多少张图、优先做什么方向？ → **缺口测算 / 排期**
- 要在某平台申请资源位、向合作方收一堆素材，怎么把规则和交期讲清楚？ → **资源需求表**
- 一堆资料要复盘整理，怎么不跑偏、不留错口径？ → **复盘框架**

仓库包含 3 个可安装 Skill、一套配置、8 个脚本、方法文档和报告模板。

### 四个主题 → 包里对应什么

| 你说的主题 | 包里落在哪 |
|---|---|
| 用户研究 / 用户分析 | `ad-material-review/references/user-analysis.md`（用户分层 × 素材标签 × CTR 交叉分析）+ `analyze.py` 的分层维度 |
| 素材管理 | `ad-material-review`（打标、索引、重命名、缺口）+ `channel-resource-table`（收素材、排交付） |
| 游戏数据复盘 | `ad-material-review`（七阶段复盘全流程、大盘 Benchmark、复用衰减、报告） |
| 复盘 / 整理方法论 | `retrospective`（弹性框架、三条底线） |

> 说明：原素材里**没有**一个叫「用户研究」的独立工具，这块能力是长在素材复盘里的（按人群分层看效率、按标签找哪类素材打动谁）。本版把它**单独抽成一份通用方法文档**，让四类主题都齐。

---

## 二、三个 Skill 一览

| Skill | 用途 | 主要产物 |
|---|---|---|
| **ad-material-review** | 投放素材复盘与效果归因（由两套同源工作流合并而成） | 打标明细、多维度 CTR 归因、大盘双口径对比、复用衰减、HTML 报告、缺口测算 |
| **channel-resource-table** | 渠道资源/素材需求表制作 | 成对交付的「全景表」（内部）+「需求表」（对外） |
| **retrospective** | 复盘 / 整理 / 总结的弹性框架 | 不产出文件，规定「这类活该怎么推进」 |

三者的关系（业务闭环）：

```
   retrospective（怎么复盘整理）
            │ 方法论贯穿
            ▼
   channel-resource-table ──→ 投放 ──→ ad-material-review ──→ 下一轮素材
   （向前看：这次收什么素材）        （向后看：做过的哪类好）
```

### 场景模板示例图

下面只展示可配置流程，不代表任何真实游戏、平台或客户项目：

```mermaid
flowchart LR
    C["配置占位符<br/>{{GAME_NAME}} / {{PLATFORM_NAME}}"] --> D["合成示例数据<br/>或获准的数据源"]
    D --> A["离线分析<br/>标签 / CTR / 复用衰减"]
    A --> R["人工复核<br/>口径与证据"]
    R --> O["模板化输出<br/>报告 / 需求表 / 下一轮计划"]
```

---

## 三、包结构

```
游戏素材复盘工作流_脱敏通用版/
├── README.md                          ← 本文件（总入口）
├── LICENSE                            ← 使用许可：可自由使用 / 修改 / 分发
├── VERSION                            ← 版本号（当前 v1.1.0）
├── CHANGELOG.md                       ← 版本变更记录
├── .gitignore                         ← 防止真实配置与数据误提交
├── 迁移到新游戏指南.md                 ★ 换一款游戏，一步一步怎么做
├── 分享包文档/
│   ├── 安装与前置条件.md               装之前要准备什么
│   ├── 使用示例与提示词.md             怎么调用、示例提示词
│   ├── 团队定制清单.md                 换团队要改哪几处
│   └── 避坑指南.md                     踩过的坑，建议先看
├── examples/                          全假数据，可安全外发
│   ├── README.md                      空跑命令
│   ├── config.demo.json               填好的示例配置
│   ├── master.sample.csv / tagged.sample.csv / labels.sample.json
│   └── bench.json / bench_materials.json
└── skills/
    ├── ad-material-review/
    │   ├── SKILL.md + 说明文档.md + README.md（技术向）
    │   ├── config/  (config.example.json / config.schema.md / presets×2)
    │   ├── scripts/ (8 个，全部读 config)
    │   ├── references/ (5 份方法论)
    │   └── assets/report_template.html
    ├── channel-resource-table/
    │   ├── SKILL.md + 说明文档.md
    │   ├── config/spec.example.json
    │   ├── scripts/ (2 个)
    │   └── references/ (5 份)
    └── retrospective/
        ├── SKILL.md + 说明文档.md
```

每个 Skill 都配有 `说明文档.md`，用图示和业务语言解释用法；`SKILL.md` 保存 Agent 执行时遵守的规则。

---

## 四、三分钟快速开始

### 方式 A：只想先看懂（不用装）
直接读 `skills/*/说明文档.md`，或看 `examples/` 里的数据长什么样。

### 方式 B：把脚本空跑一遍（不联网、不需要授权）
从**包根目录**执行（能看到本 README 和 `examples/` 的那一层）：

```bash
python skills/ad-material-review/scripts/analyze.py \
  --config examples/config.demo.json \
  --csv examples/tagged.sample.csv \
  --out examples/out/analysis.json
```
能打印出各维度 CTR 表就说明配置和脚本都正常。完整三条命令见 `examples/README.md`。

### 方式 C：装成 Skill 给 Agent 用
把 `skills/` 下的三个目录整目录拷到你的 Agent 的 skills 目录（如 `{{SKILL_ROOT}}/` 或 `{{SKILL_ROOT}}/`），
然后按 `分享包文档/安装与前置条件.md` 配好依赖即可。详见下一节。

---

## 五、安装与前置条件（摘要）

> 完整版见 `分享包文档/安装与前置条件.md`。

1. **Python 3.8+**（脚本只用标准库，无需 pip 安装）
2. **在线表格 / 智能文档能力**（`table-cli` 或你们自己的 CLI）——只在「接真实数据源」时需要；空跑分析不需要
3. **多模态看图能力**——逐张给素材图打标签时需要
4. **一份平台规则文档**（用 `channel-resource-table` 时）
5. **复制配置文件**：`cp skills/ad-material-review/config/config.example.json skills/ad-material-review/config/config.json`，按 `config.schema.md` 填真实值

> 原表一律只读。所有写操作都指向新建的子表或文档。

---

## 六、怎么迁移到别的游戏 / 平台（核心设计）

所有项目专属信息都写入 `config.json`。迁移到新项目时替换配置，不改脚本和文档。

```
        config/config.json
  游戏名·平台·子表名·字段名·标签体系·
  节点档期·对标游戏·图片域名·叙事策略
              │
      ┌───────┼────────┐
      ▼       ▼        ▼
   取数脚本  分析脚本  报告模板
   （都不写死游戏信息）
```

要改的 9 类东西：`project` / `source` / `fields` / `taxonomy` / `nodes` / `benchmark` / `thresholds` / `output` / `report`。
**一步一步的操作见《迁移到新游戏指南.md》**，逐字段说明见 `skills/ad-material-review/config/config.schema.md`。

包里还给了**两套示例标签预设**（`config/presets/`：偏暗黑幻想 / 偏科幻射击），
演示「同一套流程、两套标签」怎么工作——画风取值完全不同，但脚本、分析维度、报告模板一模一样。

---

## 七、报告叙事：一个业务规矩做成了开关

不同业务方对「报告能不能写排名、垫底」要求不同，所以做成配置开关 `report.narrative`：

| 值 | 报告写什么 | 适用 |
|---|---|---|
| `neutral` | 客观全量 | 内部复盘 |
| `positive_only` | 只写优势与环比进步；排名/分位/垫底不进报告 | 给更上层看的汇报 |
| `full` | 全量含排名 | 明确要求完整披露 |

**关键**：用 `positive_only` 时，扎心数据（排名、分位、与头部差距）**仍要算出来留档**，
只是不写进报告，交付时口头/私信告知业务方本人——「不隐瞒，但不写进给更上层看的报告」。
详见 `ad-material-review/说明文档.md` 第六节。

---

## 八、脱敏说明（本包做了什么）

| 敏感项 | 处理方式 |
|---|---|
| 游戏名 / 平台名 | 全部换成「{{GAME_NAME}}」「{{PLATFORM_NAME}}」等占位 |
| 真实 CTR / 曝光 / 金额 | 全部换成占位 `X.XX%` / `N`，或标注「示例」的编造数据 |
| 运营档期 / 版本号 | 换成「节点A/B」「档期一/二」等抽象名 |
| 用户分层名 | 换成「分层A_纯新」等抽象名 |
| 内部文档 ID / 内网链接 / CDN 网址 | 换成 `<DOCID>` / `cdn.example.com` 占位 |
| 人名、团队名、具体日期来源 | 全部移除 |
| 两套同源 skill | 合并成一套通用工作流，差异抽象成 `source.mode` 与 `report.narrative` 开关 |
| 脚本里的硬编码 | 全部抽到 config，脚本读配置，不写死任何游戏信息 |

**正式使用前**：把 `config.json` 的占位值换成真实值，把 `output.cdn_base` 换成你们平台图片域名；
不要把真实业务数据写回脚本或提交到公开仓库。

---

## 九、常见问题

**Q：不联网能用吗？**
A：分析类脚本（`analyze.py` / `benchmark.py` / `reuse_map.py` / `label_merge.py` / `rename_images.py`）读本地 CSV/JSON，完全离线可跑；取数与写表脚本需要在线表格授权。`examples/` 就是给离线空跑用的。

**Q：换成一个完全不同类型的游戏（比如卡牌、二次元）能用吗？**
A：能。改 `taxonomy` 的标签体系即可（画风/元素/福利按你的品类重写），其余流程不变。`presets/` 演示的就是两种不同品类共用一套流程。

**Q：字段跟我们表里的列名不一样怎么办？**
A：只改 `config.fields` 的「右边」（源表真实列名），脚本内部列名不用动。

**Q：一定要用在线表格吗？**
A：不强制。脚本里的在线表格调用是可选通道；把数据导出成 `master.csv` 形态后，分析与报告环节完全可离线跑。`table-cli` 相关命令可按你们环境的 CLI 替换。

**Q：为什么有两个 `说明文档.md` 和 `SKILL.md`？**
A：`说明文档.md` 面向使用者，包含业务说明和图示；`SKILL.md` 面向 Agent，保存执行规则。

---

## 十、验收与自检记录

本包按「可作为分发版」的标准复核，通过 7 项自检（逐项方法见 `分享包文档/避坑指南.md` 末尾）：

| # | 自检项 | 结果 |
|---|---|---|
| 1 | 脱敏扫描：真实游戏名 / 平台名 / 人名 / 内部文档 ID / 内网域名 / 真实业务数字 / 本地路径 | 0 命中 |
| 2 | 技能可安装：3 个 `SKILL.md` 的 frontmatter 均含 `name` / `description` / `agent_created` | 规范 |
| 3 | 零第三方依赖：全部脚本仅用 Python 标准库 + 包内模块 | 无需 `pip install` |
| 4 | 脚本语法：全部 `.py` 通过 `py_compile` | 通过 |
| 5 | 数据可解析：全部 JSON 通过解析，HTML 报告模板占位符完整 | 通过 |
| 6 | 离线空跑：`analyze.py` / `benchmark.py` / `reuse_map.py` 用假数据跑通 | 通过 |
| 7 | 包完整性：zip 校验通过、无缓存 / 临时产物、包内文件与构建目录逐一一致 | 通过 |

---

## 十一、版本 / 许可 / 维护与反馈（分发方请先看）

### 版本与改动怎么追

- 当前版本写在 `VERSION`（本版 `v1.1.0`），只此一处是版本号的准。
- 每次改动追加到 `CHANGELOG.md`：改了什么、为什么改、影响哪些文件。改脚本逻辑请升次版本号，只改文档/错别字升修订号。
- 报问题或提需求时附上版本号 + 涉及的文件名，定位会快很多。

### 许可：能怎么用

见 `LICENSE`（MIT）。可以使用、修改和再分发，但必须保留版权与许可声明。

两个条件：① 保留 `LICENSE` 文件本身；② 出问题不找原作者（模板按现状提供）。

> 本仓库采用 MIT License，版权持有人为 `Destiny-cyy`；再分发时须保留版权与许可声明。
> 若你们公司有统一许可证或保密要求，直接用你们的文件替换 `LICENSE` 即可，**不需要改包里其他内容**。

### 维护与反馈：边界说清楚

- 本包是**脱敏通用模板**，不含任何具体维护人、团队名或联系方式。
- 转发给外部前，请由分发方在 `分享包文档/团队定制清单.md` 补上「谁维护、有问题找谁、按哪套规矩改」——**这一步不做，接收方会不知道该找谁**。
- 建议把 `.gitignore` 一起保留：它挡住真实 `config.json`、`data/`、素材图、空跑产物，避免接收方填完真实数据后误提交到版本库。

### 分发前 3 项自检（发给别人之前过一遍）

1. **再扫一次敏感词**：确认没人把真实游戏名 / docid / 内网地址 / 真实数字写回文件（本版已 0 命中，但每次改动后要重扫）。
2. **确认 `config/config.json` 不存在**：包里只应有 `config.example.json` 和 `config.demo.json`；真实配置绝不进包。
3. **确认能空跑**：解压后从包根目录跑一次 `examples/README.md` 里的三条命令，能出结果再发。

---

*本包为通用工作流模板，占位符与示例数据替换后方可用于真实项目。*
