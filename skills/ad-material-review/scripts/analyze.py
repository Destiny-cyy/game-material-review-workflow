#!/usr/bin/env python3
"""阶段5 效果分析：多维度「曝光加权 CTR」聚合 + 复用衰减 + 大盘 Benchmark 排名。

核心口径（务必遵守）：
  CTR = SUM(点击) / SUM(曝光)，绝不对每行 CTR 取简单平均；
  每个结论都要带 样本量 / 曝光 / CTR 三个数；
  样本 < min_sample 的组标注「样本不足」，只给方向性结论。

支持两种输入：
  --csv ./data/tagged.csv   离线 CSV（推荐，可空跑 examples）
  --docid/--sheet           在线表格（走 table-cli SQL 聚合）

用法:
  python analyze.py --csv ./data/tagged.csv --out ./data/analysis.json
"""
import argparse
import csv
import json
import os
import statistics
from collections import defaultdict

from config_loader import load_config, T, add_config_arg


def agg(rows, keyfn, min_sample):
    g = defaultdict(lambda: [0, 0, 0])  # n, imp, clk
    for r in rows:
        k = keyfn(r) or "(空)"
        g[k][0] += 1
        g[k][1] += float(r["impressions"] or 0)
        g[k][2] += float(r["clicks"] or 0)
    res = []
    for k, (n, imp, clk) in g.items():
        ctr = clk / imp * 100 if imp else 0
        res.append({"组": k, "样本": n, "曝光": int(imp), "点击": int(clk),
                    "CTR": round(ctr, 3),
                    "标注": "样本不足" if n < min_sample else ""})
    res.sort(key=lambda x: -x["CTR"])
    return res


def reuse_decay(rows, bands):
    """按图片链接去重成唯一图，看第 N 次复用的效率衰减与曝光结构。"""
    g = defaultdict(list)
    for r in rows:
        key = r.get("image_url") or r.get("material_id")
        g[key].append(r)
    items = []
    for key, rs in g.items():
        imp = sum(float(r["impressions"] or 0) for r in rs)
        clk = sum(float(r["clicks"] or 0) for r in rs)
        items.append({"复用次数": len(rs), "曝光": imp,
                      "CTR": clk / imp * 100 if imp else 0})
    out = []
    maxb = max(bands) if bands else 4
    for b in bands:
        label = "%d次" % b if b < maxb else "%d次+" % b
        grp = [x for x in items if (x["复用次数"] == b if b < maxb else x["复用次数"] >= b)]
        if not grp:
            continue
        out.append({"档位": label, "图数": len(grp),
                    "总曝光": int(sum(x["曝光"] for x in grp)),
                    "CTR中位": round(statistics.median([x["CTR"] for x in grp]), 3),
                    "标注": "样本极小，仅参考" if len(grp) < 10 else ""})
    return out


def show(title, rows):
    print("=== %s ===" % title)
    for r in rows:
        print("  %-16s 样本%-5s 曝光%.0fw  CTR %.2f%%  %s" % (
            str(r.get("组") or r.get("档位")), r.get("样本", r.get("图数", "-")),
            r.get("曝光", r.get("总曝光", 0)) / 10000,
            r.get("CTR", r.get("CTR中位", 0)), r.get("标注", "")))


def main():
    ap = argparse.ArgumentParser()
    add_config_arg(ap)
    ap.add_argument("--csv", default="./data/tagged.csv")
    ap.add_argument("--out", default="./data/analysis.json")
    args = ap.parse_args()

    cfg = load_config(args.config)
    tax = T(cfg)
    th = cfg["thresholds"]
    min_sample = th["min_sample"]
    sep = tax.get("element_separator", "+")

    rows = list(csv.DictReader(open(args.csv, encoding="utf-8-sig")))
    res = {}
    res["整体月度"] = agg(rows, lambda r: (r["date"] or "")[:7], min_sample)
    res["节点"] = agg(rows, lambda r: r["node"], min_sample)
    res["画风"] = agg(rows, lambda r: r["style"], min_sample)
    res["福利呈现"] = agg(rows, lambda r: r["benefit"], min_sample)
    res["用户分层"] = agg(rows, lambda r: r["segment"], min_sample)

    # 画面元素：多选按「包含」口径，组间会重叠，需说明
    elems = tax["elements"]
    er = []
    for e in elems:
        sub = [r for r in rows if e in (r["elements"] or "")]
        for x in agg(sub, lambda r, _e=e: _e, min_sample):
            er.append(x)
    res["画面元素（多选包含口径，组间重叠）"] = er

    # 画风 × 福利 交叉
    res["画风x福利"] = agg(rows, lambda r: "%s×%s" % (r["style"], r["benefit"]), min_sample)

    # 复用衰减
    res["复用衰减"] = reuse_decay(rows, th["reuse_bands"])

    for k, v in res.items():
        show(k, v)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    json.dump(res, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n已写出: %s" % args.out)
    print("提醒：大盘对比必须同时给「游戏级（曝光加权）」与「素材级（单张中位）」两个口径，见 benchmark.py。")


if __name__ == "__main__":
    main()
