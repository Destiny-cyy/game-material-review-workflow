# 在线表格 / 智能文档操作要点与已知坑

> 命令走 `table-cli`（在线表格连接器）。本包脚本已封装常用调用，本文件是「出问题时翻这里」。
> 前置：连接器已连接、已授权；协议要求读写前先读子表/字段列表，参数名 `docid` 全小写。
> 换环境时命令前缀可能不同，以你们实际 CLI 为准；本文件记录的是**坑与规避思路**，不绑定具体游戏。

---

## 一、取数

```bash
table-cli smartsheet sheets list --json '{"docid": "<DOCID>"}'
table-cli smartsheet records query --docid '<DOCID>' --sql 'SELECT `字段` FROM `子表` GROUP BY `字段` LIMIT 100'
table-cli smartsheet fields list --json '{"docid": "<DOCID>", "sheet_title": "<子表>", "limit": 50}'
```

- SQL 能力边界：**不支持** 子查询、窗口函数、UNION、COALESCE、CAST；
  **支持** GROUP BY / HAVING / COUNT(DISTINCT) / SUM / CASE WHEN / LIKE / DATE_FORMAT。
- 日期字段在 SQL 里可能是 Excel 序列号，分组统计用 `DATE_FORMAT(字段, "%Y-%m")`。
- URL 字段返回 dict，取 `url` 或 `text`（`config_loader.url_of` 已处理）。
- 若窗口函数不可用，**分位改成本地算**：拉明细（设曝光门槛）到本地用 Python 算，别硬写 SQL。

---

## 二、写入打标子表

```bash
table-cli smartsheet sheets add --json '{"docid":"...","sheet_title":"<新建子表>","fields":[...]}'
table-cli smartsheet records add --json '{"docid":"...","sheet_title":"...","records":[{"values":{...}}]}'
table-cli smartsheet views update --json '{"docid":"...","sheet_title":"...","type":"update","views":[{"view_id":"...","col_infos":[...]}]}'
```

- 单选/多选写入格式：`[{"text": "选项文本"}]`（不必传 id）
- 日期写 `"YYYY-MM-DD 00:00:00"`；百分比写小数（0.0123）
- **新建字段后必须设置列宽**（规范强制），`col_infos` 传 `field_title` + `width`
- `fields update` 传单选属性时必须包含**全部**选项，否则旧选项丢失

---

## 三、已知坑（都踩过）

| 坑 | 表现 / 处理 |
|---|---|
| **命令行超长** | 一次提交几百条报 `WinError 206` → 按 **50–80 条/批**拆分（`--batch`） |
| **单次提交体积超限** | 长表追加报 `640463` → 按 **25 行/块**拆成多个文件分批 |
| **图片缓存去重** | 同一张图第二次 Read 返回 "unchanged" 看不到内容 → 复制文件并在 JPEG 头插入 COM 段（0xFFFE + 2字节长度 + 内容）生成副本再读 |
| **同链接多条记录回填** | 映射必须保留**首次出现**的 rowid（与图片文件名一致），否则回填大面积为空 |
| **内置数据表** | 智能文档的表格要用内置库 docid，不要另建独立表格，否则不挂在文档里 |
| **字段顺序** | 新字段只能追加到末尾，无法插入指定位置 |
| **选项被覆盖** | 见上，传单选属性要带全量选项 |
| **replace 后 id 失效** | `blocks update replace` 返回 `new_block_id`，旧 id 再用会**静默失败**（status=None）→ 重拉块列表 |
| **mdx 百分号** | Python 格式化 mdx 时字面 `%` 写成 `%%`，否则触发格式化报错 |
| **mdx 空锚点** | `[第六节](#)` 渲染成乱码，提示文字别用空链接 |
| **表格解析** | 智能页 markdown 的表格是 HTML `<table>`，用 `<tr><td>` 正则统计，不能用管道符 |
| **bash 反引号** | 在 bash 里生成 Markdown 时反引号会被命令替换吃掉 → 写 md 用文件写入工具，不用 shell |

---

## 四、智能文档

```bash
table-cli smartpage import --json '{"name":"标题","file_path":"绝对路径.md"}'      # 从零建文档
table-cli smartpage pages get --json '{"docid":"...","page_id":"...","content_type":"block"}'
table-cli smartpage pages append --json '{"docid":"...","page_id":"...","content_type":"markdown","file_path":"..."}'
table-cli smartpage blocks update --json '{"docid":"...","page_id":"...","method":"replace","block_id":"...","mdx":"..."}'
```

- `page_id`、`block_id` **必须从回包取，禁止构造**
- 修改局部内容用 `blocks update`，**禁止**用 overwrite 做局部替换
- 输出给用户的链接格式：`URL?_fid=<docid>`

### 读取时的两种返回
| `content_type` | 内容位置 |
|---|---|
| `markdown` | `pages[0].content_file_inner`（字符串，可直接存 .md） |
| `block` | `pages[0].file_path`（本地 JSON 路径，内容是平铺块数组） |

块对象字段：`id` / `type`（`header_1`/`header_2`/`text`/`bulleted_list`/`numbered_list`/`unspecified`=表格）/ `parent_id` / `property.title.text`。
表格块常表现为 `unspecified`，且与小标题交替出现，取 id 前务必打印 type + 文本核对。

### blocks update 三个方法
```bash
# 替换（返回 new_block_id，原 id 立即失效）
... "method":"replace","block_id":"<id>","mdx":"## 新内容"
# 插入
... "method":"insertAfter","block_id":"<id>","mdx":"..."      # 或 insertBefore
# 删除（数组批量）
... "method":"delete","block_ids":["<id1>","<id2>"]
# 追加到文档末尾
... "method":"append","mdx":"..."
```

⚠️ **replace 后必须重新拉块列表**：新 id 与旧 id 不同，用旧 id 继续操作会静默失败。
批量改文档时分脚本执行：先跑删除+替换，重拉块，再跑插入。

---

## 五、通用规避原则

1. **长内容一律写进 .py 用 subprocess 传 JSON**，避免 shell 转义与长度限制。
2. **分批 + 回读校验**：写完必须回读记录数/合并/样式，接口返回成功 ≠ 真的对了。
3. **原表只读**：所有写操作都指向**新建**子表/文档，绝不碰数据源。
4. 完整「去旧/对齐」流程见 `doc-sync.md`。
