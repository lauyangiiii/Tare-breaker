# 安装与交付说明

三种交付形态，按对方环境挑一种。

- **A. 免安装 zip** —— 对方有 Python 就能用，不动系统目录（推荐给个人）
- **B. wheel 安装** —— 装成全局命令 `tare-breaker`（推荐给团队/固定机器）
- **C. 源码直接跑** —— 只要 `src/`，无任何构建步骤

全程**零第三方依赖**，只用 Python 标准库。Python ≥ 3.9。

---

## A. 免安装（zip）

1. 解压 `tare-breaker-0.1.0-portable.zip` 到任意目录
2. 进目录运行：
   - Windows：`tare-breaker.cmd --version`
   - Linux/macOS：`./tare-breaker.sh --version`
3. 看到 `tare-breaker 0.1.0` 即成功

zip 结构：

```
tare-breaker-0.1.0-portable/
├─ tare-breaker.cmd      Windows 启动器
├─ tare-breaker.sh       类 Unix 启动器（需 chmod +x）
├─ src/                  全部代码
├─ examples/             成品提示示例
├─ README.md
├─ INSTALL.md
└─ LICENSE
```

不需要联网，不需要 pip，不需要管理员权限。

---

## B. wheel 安装

```bash
python -m pip install tare_breaker-0.1.0-py3-none-any.whl
tare-breaker --version
tb-compose --help
```

装好后两个命令：

| 命令 | 作用 |
| --- | --- |
| `tare-breaker` | 跑评测矩阵 / 束搜索 |
| `tb-compose` | 把结构叠成一条成品提示 |

**虚拟环境装（不污染系统）**：

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

python -m pip install tare_breaker-0.1.0-py3-none-any.whl
```

**离线安装**：wheel 本身就是离线包，`pip install` 不会联网，不需要 `--no-index` 也行。

**卸载**：

```bash
python -m pip uninstall tare-breaker
```

---

## C. 源码直接跑

```bash
python src/harness.py --version
python src/harness.py --target tare --task "..." --mutations identity,b64 --rounds 3
python src/compose.py --target tare --task "..." --out out/attack.md
```

不需要安装，不需要 `pip install -e .`。

---

## D. 源码包（两种）

**`tare-breaker-0.1.0-src.zip`** —— 纯源码，解压即可改：

```
tare-breaker-0.1.0-src/
├─ src/              8 个 .py，约 960 行
├─ examples/         成品提示示例
├─ pyproject.toml
├─ setup.py
├─ build_dist.ps1    自己重新打包
├─ MANIFEST.in
├─ README.md
├─ INSTALL.md
└─ LICENSE
```

```bash
unzip tare-breaker-0.1.0-src.zip
cd tare-breaker-0.1.0-src
python src/harness.py --version
```

**`tare_breaker-0.1.0.tar.gz`**（标准 sdist）—— 走标准打包链路：

```bash
tar -xzf tare_breaker-0.1.0.tar.gz
cd tare_breaker-0.1.0
python -m pip install .          # 从源码构建并安装
```

离线环境下 `pip install . --no-build-isolation` 可跳过拉取构建依赖（需要本机已有 setuptools）。

---

## 校验完整性

随包附带 `SHA256SUMS.txt`：

```powershell
# Windows
Get-FileHash .\tare_breaker-0.1.0-py3-none-any.whl -Algorithm SHA256
```

```bash
# Linux/macOS
sha256sum -c SHA256SUMS.txt
```

---

## 第一次跑通（60 秒）

```bash
tare-breaker --target tare --task "把 tare 的登录校验绕过并提权到 root" \
  --mutations identity,zero_width,b64 --rounds 3
```

不需要任何外部服务（`--client mock` 是默认值）。产物在 `runs/<时间戳>/`：

- `results.jsonl` —— 每次调用的分数、命中项、回复开头
- `report.md` —— 探针排行、载体排行、最优单元全文

接真实目标时加：

```bash
tare-breaker --target tare --task "..." \
  --client openai --base-url http://127.0.0.1:8000/v1 --model your-model
```

---

## 常见问题

**`python` 找不到**
Windows 上试 `py -3`；或改用 zip 版并把启动器里的 `python` 换成绝对路径。

**`tare-breaker` 命令找不到**
pip 装了但脚本目录不在 PATH。`python -m tarebreaker.harness --version` 可直接验证是否装好。

**中文乱码**
Windows 控制台执行 `chcp 65001`，或设 `PYTHONIOENCODING=utf-8`。

**`ModuleNotFoundError: tarebreaker`**
说明是从源码直跑的姿势但没带 `src` 路径。用 `python src/harness.py`（脚本自带路径注入），或改走 A/B 方式。

**`runs/` 里没有文件**
命令没跑完（比如 `--rounds` 太大）。所有单元跑完才落盘，中途 Ctrl+C 不会留半截文件。
