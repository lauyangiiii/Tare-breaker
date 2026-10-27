"""Strip specific paths from a git fast-export stream.

    git fast-export --all --no-data --signed-tags=strip | python tools/purge_paths.py > clean.dump
"""
import re
import sys

TARGETS = re.compile(r"^(k1|k1\.pub|keys/.*)$")
FILEMOD = re.compile(r"^M \d+ (?:[0-9a-f]{40}|[0-9a-f]{64}) (.+)$")
FILEDEL = re.compile(r"^D (.+)$")

out = []
dropped = 0
for raw in sys.stdin.buffer:
    line = raw.decode("utf-8", "surrogateescape").rstrip("\n")
    m = FILEMOD.match(line) or FILEDEL.match(line)
    if m and TARGETS.match(m.group(1).strip('"')):
        dropped += 1
        continue
    out.append(line)

sys.stdout.write("\n".join(out) + "\n")
sys.stderr.write(f"dropped {dropped} file entries\n")
