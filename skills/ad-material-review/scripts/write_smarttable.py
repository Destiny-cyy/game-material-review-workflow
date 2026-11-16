#!/usr/bin/env python3
"""阶段4 写入智能表格：新建打标子表 → 分批写记录 → 设列宽 → 回读校验。

字段与选项全部从 config.taxonomy 生成，不写死任何游戏标签。
原表只读；本脚本只新建子表 config.source.tag_sheet。

用法:
  python write_smarttable.py --csv ./data/tagged.csv
  python write_smarttable.py --csv ./data/tagged.csv --batch 50
"""
import argparse
import csv
import json
import os
import subprocess
import time

from config_loader import load_config, T, add_config_arg


PROP = {
    "single_select": lambda o: {"property_single_select": {"is_quick_add": False,
                                "options": [{"text": t, "style": 3} for t in o]}},
    "select": lambda o: {"property_select": {"is_quick_add": False,
                         "options": [{"text": t, "style": 10} for t in o]}},
    "date_time": lambda o: {"property_date_time": {"format": "yyyy-mm-dd", "auto_fill": False}},
    "number": lambda o: {"property_number": {"decimal_places": 0, "use_separate": True}},
    "percentage": lambda o: {"property_percentage": {"decimal_places": 2, "use_separate": False}},
    "text": lambda o: {},
}


def build_fields(cfg):
    """按 config.taxonomy 生成字段定义（含单选/多选选项）。"""
    t = T(cfg)
    return [
        {"title": "素材ID", "type": "text", "width": 160, "options": []},
        {"title": "投放日期", "type": "date_time", "width": 120, "options": []},
        {"title": "用户分层", "type": "single_select", "width": 160, "options": t["segments"]},
        {"title": "广告位置", "type": "text", "width": 160, "options": []},
        {"title": "节点", "type": "single_select", "width": 120,
         "options": node_options(cfg)},
        {"title": "画风", "type": "single_select", "width": 160, "options": t["style"]},
        {"title": "画面元素", "type": "select", "width": 240, "options": t["elements"]},
        {"title": "福利呈现", "type": "single_select", "width": 160, "options": t["benefit"]},
        {"title": "画面描述", "type": "text", "width": 400, "options": []},
        {"title": "打标置信度", "type": "single_select", "width": 120, "options": t["confidence"]},
        {"title": "曝光", "type": "number", "width": 160, "options": []},
        {"title": "点击", "type": "number", "width": 160, "options": []},
        {"title": "点击率", "type": "percentage", "width": 120, "options": []},
    ]


def node_options(cfg):
    n = cfg.get("nodes", {})
    return list(n.get("keywords", {}).keys()) + list(n.get("ranges", {}).keys()) + [n.get("default", "日常")]


def call(args):
    cli = os.environ.get("TABLE_TOOL_CLI", "table-cli")
    r = subprocess.run([cli] + args, capture_output=True, text=True, encoding="utf-8")
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"errcode": -1, "raw": r.stdout[:300]}


def main():
    ap = argparse.ArgumentParser()
    add_config_arg(ap)
    ap.add_argument("--csv", default="./data/tagged.csv")
    ap.add_argument("--batch", type=int, default=50, help="每批写入条数（命令行过长会报错，务必分批）")
    args = ap.parse_args()

    cfg = load_config(args.config)
    docid = cfg["source"]["docid"]
    sheet = cfg["source"]["tag_sheet"]
    sep = T(cfg).get("element_separator", "+")
    fields = build_fields(cfg)
    rows = list(csv.DictReader(open(args.csv, encoding="utf-8-sig")))

    payload = {"docid": docid, "sheet_title": sheet, "fields": []}
    for f in fields:
        item = {"field_title": f["title"], "field_type": f["type"]}
        item.update(PROP.get(f["type"], lambda o: {})(f.get("options", [])))
        payload["fields"].append(item)
    j = call(["smartsheet", "sheets", "add", "--json", json.dumps(payload, ensure_ascii=False)])
    print("建表 errcode=%s 字段数=%s" % (j.get("errcode"), len(j.get("fields", []))))
    if j.get("errcode") != 0:
        print(json.dumps(j)[:500])
        return

    types = {f["title"]: f["type"] for f in fields}

    def rec(r):
        v = {}
        for f in fields:
            t, name = f["type"], f["title"]
            raw = r.get(name, "")
            if t == "single_select":
                v[name] = [{"text": raw}] if raw else []
            elif t == "select":
                v[name] = [{"text": x} for x in str(raw).split(sep) if x]
            elif t in ("number", "percentage"):
                v[name] = float(raw or 0)
            elif t == "date_time":
                v[name] = (raw or "") + " 00:00:00" if raw else ""
            else:
                v[name] = raw
        return {"values": v}

    ok, errs = 0, []
    for i in range(0, len(rows), args.batch):
        p = {"docid": docid, "sheet_title": sheet,
             "records": [rec(r) for r in rows[i:i + args.batch]]}
        j = call(["smartsheet", "records", "add", "--json", json.dumps(p, ensure_ascii=False)])
        if j.get("errcode") == 0:
            ok += len(p["records"])
        else:
            errs.append((i, str(j)[:200]))
        time.sleep(0.3)
    print("写入 %d 条 | 失败 %s" % (ok, errs))

    v = call(["smartsheet", "views", "list", "--json",
              json.dumps({"docid": docid, "sheet_title": sheet, "limit": 5}, ensure_ascii=False)])
    views = v.get("views", [])
    if views:
        ci = [{"field_title": f["title"], "width": f.get("width", 160)} for f in fields]
        p = {"docid": docid, "sheet_title": sheet, "type": "update",
             "views": [{"view_id": views[0]["view_id"], "col_infos": ci}]}
        call(["smartsheet", "views", "update", "--json", json.dumps(p, ensure_ascii=False)])
        print("列宽已设置")

    chk = call(["smartsheet", "records", "query", "--docid", docid,
                "--sql", "SELECT COUNT(*) AS n FROM `%s`" % sheet])
    try:
        n = (json.loads(chk["values"][0]) if isinstance(chk["values"][0], str)
             else chk["values"][0])["rows"][0]["n"]
    except Exception:
        n = "?"
    print("校验记录数: %s（应为 %d）" % (n, len(rows)))


if __name__ == "__main__":
    main()
