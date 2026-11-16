# 在线表格 CLI 坑位速查（通用）

> 动手操作前必读。每条都是实际踩过的。命令前缀以你们实际 CLI 为准。

## 1. 不能用本地文件导入
本地 xlsx 导入（`doc import`）会被安全策略拦截。
→ 改用在线新建：`doc create` 建空表 + `sheet cells batchset` 写数据，完全不碰本地文件上传。

```bash
table-cli doc create --json '{"doc_type":"sheet","doc_name":"表名","sheet_title":"子表名"}'
table-cli sheet workbook get --json '{"docid":"<docid>"}'   # 拿 sheet_id
```

## 2. 表格样式范围内无法做单元格合并
互斥，两个方向都报错：
- 先 `merge set` 再 `table style add` → 合并被清掉
- 先 `table style add` 再 `merge set` → 报 `640027 表格操作参数不合法`

→ **要合并的行必须留在表格样式范围之外。**
分类条在第 3 行时，`table style add` 的范围从第 4 行（表头行）开始。
若某个区块需要横向合并，**该区块不要加表格样式**，改用静态填充 + `border set inner_*`。

## 3. `table style delete` 必须带 `yes`
```json
{"docid":"...","sheet":"...","tab_style_id":"...","yes":true}
```
不带会报 `640027 必填项`。`merge clear` 同理（高风险写入都需要 `yes`）。

## 4. `merge clear` 的 range 必须精确等于已合并区域
传大范围会报「目标区域不是已合并单元格」。要**逐个** clear。

## 5. 删除列 / 行会丢合并单元格的内容
删掉某一列后，该行合并单元格里的值可能全部变空——标题行、说明行就这么没过。
→ 发现标题行或说明行莫名变空，**先怀疑是不是被删列 / 删行带走的**，补回去即可。

## 6. 扩大合并范围会清空内容
`clear 旧范围 → set 新范围` 会清空该格。必须紧接着重写值 + 重设样式。
标题、说明、区块标题、备注这类合并行，每次调整都要走一遍「clear → set → 写值 → 设样式」。

## 7. 整体外边框只调用一次
范围变了（列数/行数增减）必须重设，但要认账：这是第二次调用。
验收时核对 `affected_range` 等于最终整体范围即可。

## 8. 读超链接要单独取
`cells get` 默认返回的可能是 `link_text`（显示文字）而不是 URL。
真实地址在 `cell.link` 里——写文档时不要照抄显示文字当链接。

## 9. 用户可能正在手动编辑表
读取结果和上次写入不一致时，**先怀疑用户在手动改**，不要盲目覆盖。
把发现告诉用户，问他要不要回填。

## 10. 没有删除在线文档的能力
CLI 通常只有 create / import / search / contents / members / names / rules。
删在线文档只能去客户端手动删。作废的旧表可以改名标「已作废」。

## 常用命令速查
```bash
# 结构
table-cli sheet workbook get --json '{"docid":"D"}'
table-cli sheet subsheets create --json '{"docid":"D","name":"子表名","position":3}'
table-cli sheet subsheets rename --json '{"docid":"D","sheet":"S","name":"新名"}'
# 数据
table-cli sheet cells batchset --json '{"docid":"D","sheet":"S","range":"A1:K20","cells":[[...]]}'
table-cli sheet cells get --json '{"docid":"D","sheet":"S","range":"A1:K20","csv":true}'
# 合并
table-cli sheet merge set --json '{"docid":"D","sheet":"S","range":"A1:K1","merge_type":"all"}'
table-cli sheet merge clear --json '{"docid":"D","sheet":"S","range":"A1:K1","yes":true}'
table-cli sheet merge get --json '{"docid":"D","sheet":"S","range":"A1:K40"}'
# 样式
table-cli sheet table style add --json '{...}'
table-cli sheet table style update --json '{...}'
table-cli sheet table style list --json '{"docid":"D","sheet":"S"}'
table-cli sheet style set --json '{"docid":"D","sheet":"S","range":"A1:K1","font_size":18}'
table-cli sheet border set --json '{"docid":"D","sheet":"S","range":"A1:K20","positions":["outer"],"style":"thin","color":"FF85888C"}'
table-cli sheet dims resize --json '{"docid":"D","sheet":"S","range":"A:K","col_widths":{...}}'
# 验收
table-cli sheet info get --json '{"docid":"D","sheet":"S","include":["merges","row_heights","col_widths"]}'
```

## Python 里调用的正确姿势
用 `subprocess.run(['table-cli', ...], capture_output=True, text=True, encoding='utf-8')`，
参数走 `--json json.dumps(payload, ensure_ascii=False)`。
**不要在 bash 里拼中文 JSON**，引号会出问题。长内容一律写进 .py 用 subprocess 传 JSON。
