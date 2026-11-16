#!/usr/bin/env python3
"""阶段3 合并打标：把各批「逐张看图」产出的 JSON 合并，按「图→投放记录」回填，生成 tagged.csv。

labels 目录里的 JSON 由子智能体逐张看图产出，格式：
  [{"img":"21","style":"风格A","elements":["单角色立绘","大字文案"],"benefit":"堆叠式","desc":"...","conf":"高"}]

回填规则（很关键）：投放记录 ≠ 创意图。一张图会被多条记录复用，
所以按图片链接找到「首次出现的 rowid」作为该图代表，用它去取标签，再回填到所有复用记录。

用法:
  python label_merge.py --labels-dir ./data --master ./data/master.csv --out ./data/tagged.csv
"""
import argparse
import csv
import glob
import json
import os

from config_loader import load_config, T, node_fn, add_config_arg


def load_labels(labels_dir, pattern):
    merged = {}
    for p in sorted(glob.glob(os.path.join(labels_dir, pattern))):
        for x in json.load(open(p, encoding="utf-8")):
            merged[str(x["img"])] = x
    return merged


def main():
    ap = argparse.ArgumentParser()
    add_config_arg(ap)
    ap.add_argument("--labels-dir", default="./data")
    ap.add_argument("--pattern", default="labels_b*.json")
    ap.add_argument("--master", default="./data/master.csv")
    ap.add_argument("--out", default="./data/tagged.csv")
    args = ap.parse_args()

    cfg = load_config(args.config)
    tax = T(cfg)
    sep = tax.get("element_separator", "+")
    judge = node_fn(cfg)

    labels = load_labels(args.labels_dir, args.pattern)
    rows = list(csv.DictReader(open(args.master, encoding="utf-8-sig")))

    # 图片链接 -> 首次出现的 rowid（与图片文件名一致）
    rep, seen = {}, set()
    for r in rows:
        u = r["image_url"]
        if u and u not in seen:
            seen.add(u)
            rep[u] = r["rowid"]

    out, miss = [], 0
    for r in rows:
        rid = rep.get(r["image_url"])
        L = labels.get(str(rid), {}) if rid else {}
        if not L:
            miss += 1
        els = L.get("elements", [])
        if isinstance(els, str):
            els_str = els
        else:
            els_str = sep.join(els)
        # judge 需要「源表列名」形态的 row，这里做一次适配
        src_row = {
            "title": r["title"], "desc": r["desc"], "date": r["date"],
        }
        fmap = {"title": "title", "desc": "desc", "date": "date"}
        out.append({
            "material_id": r["material_id"],
            "date": r["date"],
            "segment": r["segment"],
            "position": r["position"],
            "node": judge(src_row, fmap),
            "style": L.get("style", ""),
            "elements": els_str,
            "benefit": L.get("benefit", ""),
            "desc_visual": L.get("desc", ""),
            "confidence": L.get("conf", ""),
            "impressions": r["impressions"],
            "clicks": r["clicks"],
        })

    with open(args.out, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)

    err = sum(1 for o in out if o["style"] == "ERROR")
    print("标签条目 %d | 输出记录 %d | 未匹配 %d | ERROR %d" % (len(labels), len(out), miss, err))
    print("输出: %s" % args.out)
    print("提示：图片缺失/看不清应标「待人工」并给低置信度，禁止用广告文案猜画风。")


if __name__ == "__main__":
    main()
