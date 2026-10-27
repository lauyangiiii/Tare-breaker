#!/usr/bin/env python3
"""Build all four distribution artifacts, cross-platform.

    python tools/make_artifacts.py [--out dist]

Produces:
    tare_breaker-<ver>-py3-none-any.whl
    tare_breaker-<ver>.tar.gz
    tare-breaker-<ver>-portable.zip
    tare-breaker-<ver>-src.zip
    SHA256SUMS.txt
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {"dist", "runs", "build", "__pycache__", ".git", ".github", "keys", ".venv"}
EXAMPLES = [("out", "examples")]

CMD_LAUNCHERS = {
    "tare-breaker.cmd": '@echo off\r\nsetlocal\r\npython "%~dp0src\\harness.py" %*\r\n',
    "tb-compose.cmd": '@echo off\r\nsetlocal\r\npython "%~dp0src\\compose.py" %*\r\n',
}
SH_LAUNCHERS = {
    "tare-breaker.sh": '#!/usr/bin/env sh\nexec python3 "$(dirname "$0")/src/harness.py" "$@"\n',
    "tb-compose.sh": '#!/usr/bin/env sh\nexec python3 "$(dirname "$0")/src/compose.py" "$@"\n',
}

DOCS = ["README.md", "README.zh-CN.md", "INSTALL.md", "LICENSE"]
BUILD_FILES = ["pyproject.toml", "setup.py", "MANIFEST.in", ".gitignore"]


def version() -> str:
    with open(os.path.join(ROOT, "pyproject.toml"), encoding="utf-8") as fh:
        m = re.search(r'^version\s*=\s*"([^"]+)"', fh.read(), re.M)
    if not m:
        raise SystemExit("version not found in pyproject.toml")
    return m.group(1)


def run(cmd, cwd=ROOT):
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True, stdout=subprocess.DEVNULL)


def build_sdist_wheel(out: str):
    run([sys.executable, "setup.py", "bdist_wheel", "-d", out])
    run([sys.executable, "setup.py", "sdist", "-d", out])
    for junk in ("build", "tare_breaker.egg-info"):
        shutil.rmtree(os.path.join(ROOT, junk), ignore_errors=True)


def iter_src():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in filenames:
            if f.endswith(".pyc"):
                continue
            full = os.path.join(dirpath, f)
            yield full, os.path.relpath(full, ROOT).replace(os.sep, "/")


def write_zip(path: str, entries):
    """entries: iterable of (arcname, bytes, mode)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        seen = set()
        for name, data, mode in entries:
            if name in seen:
                continue
            seen.add(name)
            info = zipfile.ZipInfo(name)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (mode & 0xFFFF) << 16
            zf.writestr(info, data)


def portable_entries():
    for full, rel in iter_src():
        if rel.startswith("out/"):
            continue
        if rel in DOCS or rel in BUILD_FILES or rel.startswith("src/"):
            with open(full, "rb") as fh:
                yield rel, fh.read(), 0o644
    for name, body in CMD_LAUNCHERS.items():
        yield name, body.encode("ascii"), 0o644
    for name, body in SH_LAUNCHERS.items():
        yield name, body.encode("ascii"), 0o755
    for src_dir, dst_dir in EXAMPLES:
        d = os.path.join(ROOT, src_dir)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if f.endswith(".md"):
                with open(os.path.join(d, f), "rb") as fh:
                    yield f"{dst_dir}/{f}", fh.read(), 0o644


def src_entries():
    for full, rel in iter_src():
        if rel.startswith("out/"):
            with open(full, "rb") as fh:
                yield f"examples/{os.path.basename(full)}", fh.read(), 0o644
            continue
        with open(full, "rb") as fh:
            yield rel, fh.read(), 0o644


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "dist"))
    ap.add_argument("--skip-build", action="store_true", help="reuse existing wheel/sdist")
    args = ap.parse_args(argv)

    ver = version()
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)

    print(f"building tare-breaker {ver}")
    if not args.skip_build:
        for f in os.listdir(out):
            if f.endswith((".whl", ".tar.gz", ".zip")) or f == "SHA256SUMS.txt":
                os.remove(os.path.join(out, f))
        build_sdist_wheel(out)

    portable = os.path.join(out, f"tare-breaker-{ver}-portable.zip")
    write_zip(portable, portable_entries())
    print("wrote", portable)

    srczip = os.path.join(out, f"tare-breaker-{ver}-src.zip")
    write_zip(srczip, src_entries())
    print("wrote", srczip)

    targets = [portable, srczip]
    targets += [os.path.join(out, f) for f in sorted(os.listdir(out))
                if f.endswith(".whl") or f.endswith(".tar.gz")]
    sums = "\n".join(f"{sha256(p)}  {os.path.basename(p)}" for p in targets)
    with open(os.path.join(out, "SHA256SUMS.txt"), "w", encoding="ascii", newline="\n") as fh:
        fh.write(sums + "\n")

    print("\nartifacts:")
    for p in targets:
        print(f"  {os.path.basename(p):<40} {os.path.getsize(p) / 1024:6.1f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
