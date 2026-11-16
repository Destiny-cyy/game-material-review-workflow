#!/usr/bin/env python3
"""阶段5b 大盘 Benchmark：游戏级 + 素材级「双口径」对比。

为什么必须双口径：游戏级（曝光加权）与素材级（单张 CTR 中位）结论可能相反。
游戏级好看、素材级靠后 = 靠爆款和档期堆量，素材平均水准才是真瓶颈。两个都要算。

输入（--data-dir 下，均为示例结构）：
  bench.json            游戏×月聚合  [{"g":"游戏名","m":"YYYY-MM","imp":...,"clk":...}]
  bench_materials.json  单条素材明细 [{"g":"游戏名","imp":...,"clk":...}]

用法:
  python benchmark.py --data-dir ./examples --out ./data/benchmark.json
"""
import argparse
import json
import os
import statistics

from config_loader import load_config, add_config_arg


def load_rows(path):
    d = json.load(open(path, encoding="utf-8"))
    if isinstance(d, dict) and "rows" in d:
        return d["rows"]
    if isinstance(d, dict) and "values" in d:
        v = d["values"]
        return (json.loads(v[0]) if isinstance(v[0], str) else v[0])["rows"]
    return d if isinstance(d, list) else []


def main():
    ap = argparse.ArgumentParser()
    add_config_arg(ap)
    ap.add_argument("--data-dir", default="./examples")
    ap.add_argument("--out", default="./data/benchmark.json")
    args = ap.parse_args()

    cfg = load_config(args.config)
    b = cfg["benchmark"]
    target = b["target"]
    aliases = b["aliases"]
    peers = b["peers"]
    months = b["months"]
    gmin = b["game_min_impressions"]
    mmin = b["material_min_impressions"]

    def canon(g):
        """游戏名变体归一：命中 aliases 的一律算作 target。"""
        return target if g in aliases else g

    g_rows = load_rows(os.path.join(args.data_dir, "bench.json"))
    res = {"目标": target, "名称变体已合并": aliases, "对标": peers, "游戏级月度": {}}

    for m in months:
        gm = {}
        for r in g_rows:
            if r.get("m") == m:
                g = canon(r.get("g"))
                a = gm.setdefault(g, [0, 0])
                a[0] += r.get("imp", 0) or 0
                a[1] += r.get("clk", 0) or 0
        gm = {g: v for g, v in gm.items() if v[0] >= gmin}
        ranked = sorted(gm.items(), key=lambda kv: -(kv[1][1] / kv[1][0] if kv[1][0] else 0))
        ctrs = [v[1] / v[0] * 100 for v in gm.values() if v[0]]
        entry = {"中位": round(statistics.median(ctrs), 3) if ctrs else 0, "游戏数": len(gm)}
        for g in [target] + peers:
            if g in gm:
                imp, clk = gm[g]
                rank = [i + 1 for i, (k, _) in enumerate(ranked) if k == g][0]
                entry[g] = {"ctr": round(clk / imp * 100, 3) if imp else 0,
                            "rank": rank, "total": len(gm),
                            "pct": round((1 - rank / len(gm)) * 100), "imp": imp}
        res["游戏级月度"][m] = entry

    # 游戏级全周期
    allg = {}
    for r in g_rows:
        g = canon(r.get("g"))
        a = allg.setdefault(g, [0, 0])
        a[0] += r.get("imp", 0) or 0
        a[1] += r.get("clk", 0) or 0
    allr = {g: {"ctr": c / i * 100, "imp": i} for g, (i, c) in allg.items() if i >= gmin}
    ranked = sorted(allr.items(), key=lambda kv: -kv[1]["ctr"])
    res["游戏级全周期"] = {"中位": round(statistics.median([v["ctr"] for v in allr.values()]), 3),
                          "游戏数": len(allr)}
    for g in [target] + peers:
        if g in allr:
            rank = [i + 1 for i, (k, _) in enumerate(ranked) if k == g][0]
            res["游戏级全周期"][g] = {"ctr": round(allr[g]["ctr"], 3), "rank": rank,
                                      "total": len(allr), "pct": round((1 - rank / len(allr)) * 100),
                                      "imp": allr[g]["imp"]}

    # 素材级全周期（单张中位）
    mpath = os.path.join(args.data_dir, "bench_materials.json")
    if os.path.exists(mpath):
        m_rows = [r for r in load_rows(mpath) if (r.get("imp", 0) or 0) >= mmin]
        byg = {}
        for r in m_rows:
            byg.setdefault(canon(r.get("g")), []).append(
                (r["clk"] / r["imp"] * 100) if r["imp"] else 0)
        allv = sorted(v for vs in byg.values() for v in vs)
        res["素材级全周期"] = {"中位": round(statistics.median(allv), 3) if allv else 0,
                              "素材数": len(m_rows)}
        for g in [target] + peers:
            if g in byg:
                vals = byg[g]
                g_med = statistics.median(vals)
                below = sum(1 for v in allv if v <= g_med)
                res["素材级全周期"][g] = {"中位": round(g_med, 3), "n": len(vals),
                                          "分位": round(below / len(allv) * 100) if allv else 0}

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    json.dump(res, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("已写出: %s" % args.out)
    print("提醒：排名/分位是否进报告由 config.report.narrative 决定；")
    print("      即便不进报告也要算出来留档，并在交付时口头告知业务方本人。")
    print(json.dumps(res, ensure_ascii=False, indent=1)[:1500])


if __name__ == "__main__":
    main()
