# 智能文档对齐与去旧流程

> 适用场景：口径升级（标签体系改版）、结论重算、新增章节后，需要把已发布的在线文档「对齐到最新」。
> 原则：**文档里只留一套现行口径**，不留旧版本、不留修订史。

---

## 核心原则

1. **替换而非叠加**：口径变了就改原章节，**不要**新增一节然后留着旧节 + 一句「现行口径见第 X 节」。业务方不会翻，看到的就是旧结论。
2. **修订说明类章节定稿即删**：「本次改了什么」「v1→v2 变化」这类内容只在过程中有用，进入交付文档后是噪音。
3. **锚点块不动**：索引表、内置数据表这类业务方在用的资产，除非明确要求，一律不动（用户会明说「索引表别改」）。
4. **数据不搬家丢失**：删除旧章节前，先确认其中的明细（表/数字）已在新位置落地。

---

## 五步流程

### 1. 拉块，建地图
```bash
table-cli smartpage pages get --json '{"docid":"...","page_id":"...","content_type":"markdown"}'   # 看内容
table-cli smartpage pages get --json '{"docid":"...","page_id":"...","content_type":"block"}'      # 拿 block_id
```
- markdown 模式内容在 `pages[0].content_file_inner`；block 模式返回 `pages[0].file_path`（本地 JSON）
- block JSON 是**平铺数组**，字段：`id` / `type` / `parent_id` / `property.title.text`
- 先按 `parent_id == page_id` 过滤出顶层块，打印 `id + type + 文本前 60 字`，得到章节地图

### 2. 扫描残留
在 markdown 全文中 grep 旧口径关键词，列出所有命中块：旧版本号、旧标签名、旧小节号、过渡措辞（「较 v1」「与 v1 一致」「本次修订」）。

### 3. 删除
```bash
table-cli smartpage blocks update --json '{"docid":"...","page_id":"...","method":"delete","block_ids":["id1","id2"]}'
```
- `block_ids` 是数组，可批量；建议每批 ≤12 个便于核对
- 删标题 + 其下内容块时，把整节所有块一起删

### 4. 改标题与插入新内容
```bash
... "method":"replace","block_id":"<id>","mdx":"## 新标题"
... "method":"insertAfter","block_id":"<id>","mdx":"| 列 | 列 |\n|---|---|\n| a | b |"
```
- mdx 支持 markdown 表，接口会渲染成表格块（返回几十个块 id 是正常的）
- **内容顺序**：先 delete，再 replace/insertAfter

### 5. 校验
重新拉 markdown，确认：
- [ ] 旧口径关键词全文命中 **0**（版本号、旧标签名、旧小节号、过渡措辞）
- [ ] 章节编号连续、无重复标题
- [ ] 锚点块内容未变（如索引表链接条数仍是 N）
- [ ] 新增表格渲染成了 `<table>` 而非纯文本

---

## 已知坑

| 坑 | 表现 / 处理 |
|---|---|
| **replace 会换新 id** | 返回 `new_block_id`，原 id 立即失效。紧接着用旧 id 做 `insertAfter` 会**静默失败** → 改一批后必须**重新拉块列表**再继续 |
| **小标题与表格块交替** | 小标题块和 `unspecified` 表格块相邻，容易取错 id → 取 id 前先打印 type + 文本核对 |
| **mdx 里的百分号** | 用 Python 格式化时字面 `%` 要写成 `%%` |
| **空锚点链接** | `[第六节](#)` 渲染成乱码，提示文字别用空链接 |
| **命令行超长** | 长内容一律写进 .py 用 `subprocess` 传 JSON |
| **表格解析** | 智能页 markdown 表格是 HTML `<table>`，统计行数用 `<tr><td>` 正则 |

---

## 改完怎么说

向用户汇报时按「**删了什么 / 改了什么 / 新增了什么 / 没动什么**」四段说，并给出校验结果
（如「旧口径关键词命中 0 条，N 条索引链接未变」）。让用户一眼确认锚点资产安全。
