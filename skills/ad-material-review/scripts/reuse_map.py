#!/usr/bin/env python3
"""素材复用与衰减明细：投放记录 → 唯一创意图，输出每张图的复用次数与效率。

背景：一张创意图会被多条投放记录复用（不同人群 / 日期 / 广告位各记一行）。
只看「记录维度 CTR」会掩盖「老图反复投还有没有效」这个问题。

用法:
  python reuse_map.py --master ./data/master.csv --tagged ./data/tagged.csv --out ./data/reuse_map.csv
"""
import argparse
import csv
import os
import statistics
from collections import OrderedDict

from config_loader import load_config, add_config_arg


def pick(fieldnames, *keys):
    """按关键字容错取列名：优先完全匹配，其次包含匹配。"""
    for k in keys:
        if k in fieldnames:
            return k
    for k in keys:
        for f in fieldnames:
            if k in f:
                return f
    return None


def main():
    ap = argparse.ArgumentParser()
    add_config_arg(ap)
    ap.add_argument("--master", default="./data/master.csv")
    ap.add_argument("--tagged", default=None, help="打标 CSV（可选），用于带出画风/福利")
    ap.add_argument("--out", default="./data/reuse_map.csv")
    ap.add_argument("--min-impression", type=float, default=0, help="忽略曝光低于该值的记录")
    args = ap.parse_args()

    cfg = load_config(args.config)
    rows = list(csv.DictReader(open(args.master, encoding="utf-8-sig")))
    if not rows:
        raise SystemExit("主表为空")

    c_id = pick(rows[0].keys(), "material_id", "素材ID", "素材id")
    c_img = pick(rows[0].keys(), "image_url", "图片链接", "原图链接")
    c_imp = pick(rows[0].keys(), "impressions", "曝光UV", "曝光")
    c_clk = pick(rows[0].keys(), "clicks", "点击UV", "点击")
    c_seg = pick(rows[0].keys(), "segment", "用户分层", "广告类型")
    for name, col in [("素材ID", c_id), ("图片链接", c_img), ("曝光", c_imp), ("点击", c_clk)]:
        if not col:
            raise SystemExit("主表缺少列：%s（现有：%s）" % (name, ",".join(rows[0].keys())))

    tag = {}
    if args.tagged and os.path.exists(args.tagged):
        trs = list(csv.DictReader(open(args.tagged, encoding="utf-8-sig")))
        t_id = pick(trs[0].keys(), "material_id", "素材ID") if trs else None
        for t in trs:
            tid = t.get(t_id) if t_id else None
            if tid:
                tag[str(tid).strip()] = t

    groups = OrderedDict()
    for r in rows:
        imp = float(r[c_imp] or 0)
        if imp < args.min_impression:
            continue
        key = (r[c_img] or "").strip()
        if not key:
            continue
        groups.setdefault(key, []).append(r)

    out = []
    for i, (img, recs) in enumerate(groups.items(), 1):
        imp = sum(float(r[c_imp] or 0) for r in recs)
        clk = sum(float(r[c_clk] or 0) for r in recs)
        rep = recs[0]
        t = tag.get(str(rep[c_id]).strip(), {})
        out.append({
            "序号": i,
            "代表素材ID": rep[c_id],
            "画风": t.get("style", ""),
            "福利呈现": t.get("benefit", ""),
            "复用次数": len(recs),
            "同图各条CTR": "/".join(
                "%.2f%%" % (float(r[c_clk] or 0) / float(r[c_imp] or 1) * 100) for r in recs),
            "同图加权CTR": round(clk / imp * 100, 2) if imp else 0,
            "同图总曝光": int(imp),
            "同图用户分层": "/".join(str(r.get(c_seg, "")) for r in recs) if c_seg else "",
            "原图链接": img,
        })

    if not out:
        raise SystemExit("无有效数据")
    with open(args.out, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    print("已写出 %s：%d 张唯一图（来自 %d 条投放记录）" % (args.out, len(out), len(rows)))

    bands = cfg["thresholds"]["reuse_bands"]
    maxb = max(bands)
    print("\n=== 复用分档 × 效率 ===")
    for b in bands:
        grp = [x for x in out if (x["复用次数"] == b if b < maxb else x["复用次数"] >= b)]
        if not grp:
            continue
        med = statistics.median([x["同图加权CTR"] for x in grp])
        imp = sum(x["同图总曝光"] for x in grp)
        flag = "  (样本极小，仅参考)" if len(grp) < 10 else ""
        label = "%d 次" % b if b < maxb else "%d 次+" % b
        print("  %-8s 图数%-5d CTR中位 %.2f%%  合计曝光 %.0fw%s" % (
            label, len(grp), med, imp / 10000, flag))
    print("\n注意：复用分档只是相关性，不是因果（也可能是「好图才被反复投，但投到后面人群疲了」）。")


if __name__ == "__main__":
    main()
