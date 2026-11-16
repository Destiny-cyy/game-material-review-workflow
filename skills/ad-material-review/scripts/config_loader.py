#!/usr/bin/env python3
"""公共配置读取模块：所有脚本从这里读 config，不写死任何游戏/平台专属信息。

查找顺序：
  1) 命令行 --config 指定路径
  2) 环境变量 AD_REVIEW_CONFIG
  3) 本包 config/config.json（正式）
  4) 本包 config/config.example.json（示例，仅用于空跑演示）

用法（在其他脚本里）：
  from config_loader import load_config, F
  cfg = load_config()
  f = F(cfg)                       # 列名映射
  print(f["impressions"])          # -> "曝光UV" 或你在 config 里配的真实列名
"""
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)
_DEFAULT = os.path.join(_PKG, "config", "config.json")
_EXAMPLE = os.path.join(_PKG, "config", "config.example.json")


def load_config(path=None):
    """加载配置。返回 dict。

    显式指定路径（--config / 环境变量）但文件不存在时直接报错，
    避免「以为配置生效、其实悄悄用了示例」这种误导。
    未显式指定且正式 config.json 不存在时，才回退到示例配置空跑演示。
    """
    explicit = path or os.environ.get("AD_REVIEW_CONFIG")
    if explicit:
        if not os.path.exists(explicit):
            raise SystemExit("[config_loader] 指定的配置文件不存在：%s" % explicit)
        p = explicit
    elif os.path.exists(_DEFAULT):
        p = _DEFAULT
    else:
        p = _EXAMPLE
        print("[config_loader] 未找到 config.json，本次使用示例配置（config.example.json）空跑演示。")
    with open(p, encoding="utf-8") as fh:
        cfg = json.load(fh)
    # 合并 preset（可选）：config 里写 "preset": "preset.A.json" 即套用该标签体系
    preset = cfg.get("preset")
    if preset:
        pp = os.path.join(_PKG, "config", "presets", preset)
        if os.path.exists(pp):
            with open(pp, encoding="utf-8") as fh:
                pre = json.load(fh)
            for k in ("taxonomy", "nodes"):
                if k in pre:
                    cfg[k] = {**cfg.get(k, {}), **pre[k]}
    return cfg


def F(cfg):
    """返回「内部列名 -> 源表真实列名」映射。"""
    return cfg["fields"]


def T(cfg):
    """返回标签体系 taxonomy。"""
    return cfg["taxonomy"]


def node_fn(cfg):
    """按 config.nodes 构造 节点判定函数（关键词优先，其次日期区间）。"""
    n = cfg.get("nodes", {})
    kw = n.get("keywords", {})
    ranges = n.get("ranges", {})
    default = n.get("default", "日常")

    def judge(row, f):
        text = (row.get(f["title"], "") or "") + " " + (row.get(f["desc"], "") or "")
        for name, words in kw.items():
            for w in words:
                if w and w in text:
                    return name
        d = row.get(f["date"], "") or ""
        for name, span in ranges.items():
            if isinstance(span, (list, tuple)) and len(span) == 2:
                if span[0] <= d <= span[1]:
                    return name
        return default
    return judge


def add_config_arg(parser):
    """统一给各脚本加 --config 参数。"""
    parser.add_argument("--config", default=None,
                        help="配置文件路径；缺省读 config/config.json（无则回退示例）")
    return parser


def url_of(v):
    """URL 字段可能是 dict（在线表格），统一取字符串。"""
    if isinstance(v, dict):
        return v.get("url") or v.get("text") or ""
    return v or ""
