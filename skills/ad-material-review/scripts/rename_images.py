#!/usr/bin/env python3
"""按标签重命名素材图：编号_画风-元素-福利_素材ID.jpg（先 dry-run 预览，确认后再 --apply）。

文件名用 config.taxonomy.element_separator 连接多选元素；
'/'、':' 等是 Windows 非法字符，脚本会自动替换并做重名 / 非法字符检查。

用法:
  python rename_images.py --map ./data/tagged.csv --dir ./data/素材图            # 预览
  python rename_images.py --map ./data/tagged.csv --dir ./data/素材图 --apply     # 执行
"""
import argparse
import csv
import os

from config_loader import load_config, add_config_arg


def sanitize(s):
    for c in '\\/:*?"<>|':
        s = s.replace(c, "-")
    return s.strip()


def build(row, no, sep):
    els = (row.get("elements") or "未标注").replace("/", sep)
    return "%03d_%s-%s-%s_%s.jpg" % (
        no, sanitize(row.get("style") or "未标注"), sanitize(els),
        sanitize(row.get("benefit") or "未标注"), sanitize(str(row.get("material_id") or "")))


def main():
    ap = argparse.ArgumentParser()
    add_config_arg(ap)
    ap.add_argument("--map", default="./data/tagged.csv", help="打标 CSV")
    ap.add_argument("--dir", default="./data/素材图", help="素材图目录（当前文件名为 <编号>.jpg）")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--out", default=None, help="输出 旧名→新名 映射 CSV")
    args = ap.parse_args()

    cfg = load_config(args.config)
    sep = cfg["taxonomy"].get("element_separator", "+")
    rows = list(csv.DictReader(open(args.map, encoding="utf-8-sig")))
    seen, plan = set(), []
    for r in rows:
        key = r.get("material_id")
        if key in seen:
            continue
        seen.add(key)
        cur = os.path.join(args.dir, "%s.jpg" % r.get("rowid", ""))
        if not os.path.exists(cur):
            continue
        new = build(r, int(os.path.basename(cur).split(".")[0]) if os.path.basename(cur).split(".")[0].isdigit() else len(plan) + 1, sep)
        plan.append((cur, os.path.join(args.dir, new), new))

    if not plan:
        print("没有可重命名的文件（检查 --dir 与 CSV 的 rowid 是否对得上）。")
        return
    names = [p[2] for p in plan]
    dup = len(names) - len(set(names))
    illegal = [n for n in names if any(c in n for c in '\\/:*?"<>|')]
    print("计划 %d 个 | 重名 %d | 非法字符 %d | 最长 %d 字符" % (
        len(plan), dup, len(illegal), max(len(n) for n in names)))
    for p in plan[:10]:
        print("  %s -> %s" % (os.path.basename(p[0]), p[2]))

    if dup or illegal:
        print("存在问题，已中止。")
        return
    if not args.apply:
        print("\n(dry-run) 确认无误后加 --apply 执行。原图不会被删除，只是改名。")
        return

    done, errs = 0, []
    for cur, tgt, new in plan:
        if os.path.basename(cur) == new:
            continue
        if os.path.exists(tgt):
            errs.append(("exists", new))
            continue
        os.rename(cur, tgt)
        done += 1
    print("已重命名 %d | 错误 %s" % (done, errs))

    if args.out:
        with open(args.out, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["原文件名", "新文件名", "素材ID"])
            for cur, tgt, new in plan:
                w.writerow([os.path.basename(cur), new, new.rsplit("_", 1)[-1].replace(".jpg", "")])
        print("映射表: %s" % args.out)


if __name__ == "__main__":
    main()
