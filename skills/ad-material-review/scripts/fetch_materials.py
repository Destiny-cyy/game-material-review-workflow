#!/usr/bin/env python3
"""阶段1 取数：从在线表格拉投放明细 → master.csv，并按图片链接去重下载唯一创意图。

两种方式（由 config.source.mode 决定）：
  own_ledger    自有投放台账：直接查明细子表
  market_table  平台大盘表：按游戏名过滤目标游戏（含 aliases 变体）后取明细

原表一律只读；本脚本只 SELECT、只下载图片，不写回任何表。

用法:
  python fetch_materials.py
  python fetch_materials.py --config path/to/config.json --out-dir ./data
  python fetch_materials.py --raw-json ./snapshot.json   # 离线：从已导出的 JSON 快照生成，不联网
"""
import argparse
import concurrent.futures
import csv
import json
import os
import subprocess
import urllib.request

from config_loader import load_config, F, add_config_arg, url_of


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")


def fetch_rows(cfg):
    """按 mode 构造 SQL 并查询在线表格。返回明细行 list[dict]。"""
    s, f = cfg["source"], F(cfg)
    docid = s["docid"]
    sheet = s["sheet"]
    cols = [f["material_id"], f["date"], f["segment"], f["position"],
            f["title"], f["desc"], f["image_url"], f["video_url"],
            f["impressions"], f["clicks"]]
    sel = ", ".join("`%s`" % c for c in cols)
    where = ""
    if s.get("mode") == "market_table":
        names = cfg["benchmark"]["aliases"]
        cond = " OR ".join("`%s` = '%s'" % (f["game"], n.replace("'", "''")) for n in names)
        where = " WHERE (%s)" % cond
    sql = 'SELECT %s FROM `%s`%s ORDER BY `%s` ASC LIMIT 5000' % (
        sel, sheet, where, f["date"])
    cli = os.environ.get("TABLE_TOOL_CLI", "table-cli")
    r = run([cli, "smartsheet", "records", "query", "--docid", docid, "--sql", sql])
    j = json.loads(r.stdout)
    vals = j["values"]
    return (json.loads(vals[0]) if isinstance(vals[0], str) else vals[0])["rows"]


def rows_from_snapshot(path):
    """离线模式：从已导出的 JSON 快照读明细（结构与在线查询回包一致）。"""
    d = json.load(open(path, encoding="utf-8"))
    vals = d["values"]
    return (json.loads(vals[0]) if isinstance(vals[0], str) else vals[0])["rows"]


def to_master(rows, cfg):
    f = F(cfg)
    out = []
    for i, r in enumerate(rows, 1):
        out.append({
            "rowid": i,
            "material_id": str(r.get(f["material_id"]) or ""),
            "date": r.get(f["date"]) or "",
            "segment": r.get(f["segment"]) or "",
            "position": r.get(f["position"]) or "",
            "title": r.get(f["title"]) or "",
            "desc": r.get(f["desc"]) or "",
            "image_url": url_of(r.get(f["image_url"])),
            "video_url": url_of(r.get(f["video_url"])),
            "impressions": r.get(f["impressions"]) or 0,
            "clicks": r.get(f["clicks"]) or 0,
        })
    return out


def download(item, img_dir, referer):
    rid, u = item
    path = os.path.join(img_dir, "%s.jpg" % rid)
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return rid, "skip"
    headers = {"User-Agent": "Mozilla/5.0"}
    if referer:
        headers["Referer"] = referer
    try:
        req = urllib.request.Request(u, headers=headers)
        data = urllib.request.urlopen(req, timeout=30).read()
        with open(path, "wb") as fh:
            fh.write(data)
        return rid, "ok"
    except Exception as e:
        return rid, "ERR %s" % e


def main():
    ap = argparse.ArgumentParser()
    add_config_arg(ap)
    ap.add_argument("--out-dir", default=None, help="输出目录，缺省用 config.output.data_dir")
    ap.add_argument("--raw-json", default=None, help="离线快照 JSON，给了就不联网")
    ap.add_argument("--no-download", action="store_true", help="只生成 master.csv，不下图")
    args = ap.parse_args()

    cfg = load_config(args.config)
    out_dir = args.out_dir or cfg["output"]["data_dir"]
    img_dir = cfg["output"]["image_dir"]
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(img_dir, exist_ok=True)

    rows = rows_from_snapshot(args.raw_json) if args.raw_json else fetch_rows(cfg)
    out = to_master(rows, cfg)

    master = os.path.join(out_dir, "master.csv")
    with open(master, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)

    seen, uniq = set(), []
    for r in out:
        if r["image_url"] and r["image_url"] not in seen:
            seen.add(r["image_url"])
            uniq.append((r["rowid"], r["image_url"]))

    errs = []
    if not args.no_download:
        referer = cfg["output"].get("referer", "")
        with concurrent.futures.ThreadPoolExecutor(8) as ex:
            res = list(ex.map(lambda it: download(it, img_dir, referer), uniq))
        errs = [r for r in res if r[1] not in ("ok", "skip")]

    print("投放记录 %d 条 | 唯一创意图 %d 张 | 下图失败 %d" % (len(out), len(uniq), len(errs)))
    print("主表: %s" % master)
    print("图片: %s" % img_dir)
    print("口径提示：一条投放记录 = 一次投放；一张图可能被多条记录复用。交付时务必区分这两个数。")
    if errs:
        print("失败明细: %s" % errs[:10])


if __name__ == "__main__":
    main()
