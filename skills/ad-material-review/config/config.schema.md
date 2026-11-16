# 配置文件字段说明（config.schema）

> 一句话：**所有游戏专属信息只写在 `config.json` 一份文件里**。换游戏 = 换配置，不动脚本、不动方法论文档。
> 本包自带的 `config.example.json` 是**示例**（全是占位和假数据），正式使用前复制成 `config.json` 填写。

## 怎么开始（三步）

```bash
cd skills/ad-material-review
cp config/config.example.json config/config.json
# 用任意文本编辑器打开 config.json，按下面说明改
```

脚本默认读取 `config/config.json`；也可以用 `--config 路径` 指定别的文件（方便同时跑多款游戏）。

---

## 各区块什么意思

### project —— 项目身份
| 字段 | 填什么 | 影响哪里 |
|---|---|---|
| `game_name` | 目标游戏名 | 报告标题、口径声明 |
| `game_code` | 短代号（英文/数字） | 输出文件名前缀 |
| `game_genre` | 品类（如 RPG / 射击 / 卡牌） | 只作说明，不参与计算 |
| `platform` / `channel` | 投放平台、渠道名 | 报告标题、说明文字 |
| `period` / `focus_month` | 数据区间、重点月份 | 口径声明、报告聚焦 |
| `language` | 输出语言 | 报告文案 |

### source —— 数据从哪来
| 字段 | 填什么 |
|---|---|
| `mode` | `own_ledger`（自有投放台账，字段全）或 `market_table`（平台大盘表，按游戏名过滤） |
| `docid` / `sheet` | 投放明细所在的文档 ID 与子表名 |
| `bench_docid` / `bench_sheet` | 大盘表文档 ID 与子表名（做 Benchmark 才需要） |
| `tag_sheet` | **新建**的打标子表名 |
| `readonly` | 恒为 `true`。原表只读，打标只写新子表 |

> 两种 mode 的差别：自有台账一般带「人群分层 / 广告位置」字段，能做用户分析；大盘表通常只有投放结果与图片链接，做不了分层分析——需要时从广告后台导出补充。

### fields —— 列名对照表（最容易踩坑）
左边是工作流内部统一列名（**不要改**），右边是你源表里的**真实列名**（按实际改）。

| 内部名 | 含义 |
|---|---|
| `material_id` | 素材唯一编号 |
| `date` | 投放日期 |
| `segment` | 人群分层（广告类型） |
| `position` | 广告位置 |
| `title` / `desc` | 广告标题 / 描述 |
| `image_url` / `video_url` | 图片 / 视频链接 |
| `impressions` / `clicks` | 曝光数 / 点击数 |
| `game` | 游戏名（大盘表用） |

> 源表是 URL 字段（返回 dict）也没关系，取数脚本会自动取 `url` / `text`。

### taxonomy —— 视觉标签体系
| 字段 | 说明 |
|---|---|
| `style` | 画风，**单选、互斥穷尽** |
| `elements` | 画面元素，**多选**，最多 `element_max` 个 |
| `benefit` | 福利/奖励呈现方式，单选 |
| `segments` | 人群分层取值，需与源表 `segment` 列实际值一致 |
| `confidence` | 打标置信度 |
| `element_separator` | 多选值写入表格时的分隔符 |

**两套示例预设**在 `presets/`：一套偏暗黑幻想、一套偏科幻射击，用来演示「同一套流程、两套标签」怎么工作。它们只是示例，按你的游戏改。

### nodes —— 运营节点（版本档期）
- `keywords`：标题/描述里出现关键词就判为该节点。
- `ranges`：按投放日期落入区间判节点。
- `default`：都不命中时的兜底值（一般填「日常」）。
- ⚠️ 档期日期多为**推断值**，每次复盘前必须向业务确认，确认后只改这里，脚本不用动。

### benchmark —— 大盘对比
| 字段 | 说明 |
|---|---|
| `target` | 目标游戏名 |
| `aliases` | 同一游戏在表里的**所有名字变体**，必须合并后再算 |
| `peers` | 对标游戏（题材/量级接近） |
| `months` | 参与对比的月份 |
| `game_min_impressions` / `material_min_impressions` | 参评门槛，防小样本刷榜 |

### thresholds —— 统计门槛
`min_sample`（低于它标注「样本不足」）、`top_material_min_impressions`（TOP 素材排序门槛）、`reuse_bands`（复用分档）。

### output —— 输出与链接口径
| 字段 | 说明 |
|---|---|
| `data_dir` / `image_dir` | 本地中间产物目录与图片目录（**仅离线看图用**） |
| `cdn_base` | 你们平台的图片 CDN 域名示例值（`https://cdn.example.com` 是占位，务必替换） |
| `referer` | 下图时的 Referer，有些 CDN 会校验 |
| `link_policy` | 恒为 `cdn_only`：对外产物只放网址，禁止本地路径 |

### report —— 报告叙事开关
不同业务方对「能不能写排名/垫底」要求不同，用开关控制，**不写死在方法论里**：

| 字段 | 说明 |
|---|---|
| `narrative` | `neutral` 客观全量 / `positive_only` 只写优势与进步 / `full` 全量含排名 |
| `show_rank` | 是否展示排名与分位 |
| `show_head_game_names` | 是否列出大盘头部游戏名 |
| `peer_compare_requires_impressions` | 对标对比是否强制带曝光分母（建议恒为 true） |

> 用 `positive_only` 时：排名、分位、垫底、与头部差距等数据**仍要算**（内部留档），只是不写进对外报告，交付时口头/私信告知业务方本人。这叫「不隐瞒，但不写进给更上层看的报告」。

---

## 迁移检查清单（换一款游戏时逐条过）

- [ ] `project` 全改（游戏名、平台、区间）
- [ ] `source` 的 docid / sheet 改对，`mode` 选对，`readonly` 保持 true
- [ ] `fields` 与源表真实列名逐一核对
- [ ] `taxonomy` 换成该游戏的标签体系（或复制一份 preset 再改）
- [ ] `nodes` 档期日期向业务确认过
- [ ] `benchmark.aliases` 收齐所有游戏名变体；`peers` 换成同题材对标
- [ ] `output.cdn_base` / `referer` 换成真实图片域名
- [ ] `report.narrative` 与业务方确认过
- [ ] 改完跑一次 `--check` 或空跑 examples，确认脚本读得到配置

> 更详细的一步一步操作见包根目录的 **《迁移到新游戏指南.md》**。
