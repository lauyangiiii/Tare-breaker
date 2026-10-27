"""python -m tarebreaker [子命令] —— 等价于 tare-breaker。"""
import sys

from .harness import main

if __name__ == "__main__":
    sys.exit(main())
