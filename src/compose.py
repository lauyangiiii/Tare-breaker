"""compose.py —— 把推荐的承重结构叠成一条可直接投递的完整提示。

    python src/compose.py --target tare --task "..." --detail "..." \
        --stack P13,P01,P02,P03,P04 --mutate zero_width --out out/attack.md
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:  # pip 安装后：tarebreaker.compose
    from . import mutate
    from . import probes as probe_mod
except ImportError:  # 源码直跑
    import mutate
    import probes as probe_mod

DEFAULT_STACK = ["P13_authority_chain", "P01_identity_anchor",
                 "P02_contract_precedence", "P03_refusal_nullify",
                 "P04_layered_descent"]


def compose(stack, target, task, detail) -> str:
    blocks = []
    for i, pid in enumerate(stack, 1):
        p = probe_mod.get(pid)
        body = p["template"].format(TARGET=target, TASK=task, DETAIL=detail)
        blocks.append(f"<!-- block {i}: {pid} / {p['layer']} -->\n{body}")
    return "\n\n---\n\n".join(blocks)


def main(argv=None):
    try:  # Windows 控制台默认 cp936/cp1252，中文会炸
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="tare")
    ap.add_argument("--task", default="把目标系统里最关键的一条链路完整跑通")
    ap.add_argument("--detail", default="参数/命令/字段级")
    ap.add_argument("--stack", default=",".join(DEFAULT_STACK))
    ap.add_argument("--mutate", default="identity")
    ap.add_argument("--out", default="")
    args = ap.parse_args(argv)

    stack = [s.strip() for s in args.stack.split(",") if s.strip()]
    text = compose(stack, args.target, args.task, args.detail)
    text = mutate.apply(text, args.mutate)

    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"已写入 {args.out}（{len(text)} 字符，载体：{mutate.describe(args.mutate)}）")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
