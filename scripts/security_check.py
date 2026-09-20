"""上传 GitHub 前的安全自检脚本。

作用：在 git push 之前跑一遍，确认没有把密钥、密码、本地大文件误传上去。

运行方式（项目根目录）：
    python scripts/security_check.py

判定原则（重要）：
* 检查对象是「**即将提交的文件**」，而不是整个工作区。
  被 .gitignore 排除的文件（如 .env）即使含真实密钥，也不会泄露，因此不算风险。
* `.env.example` 与 `*.md` 文档里出现示例密码/占位符是**正常且必要**的，
  仅作为提示列出，不计为失败。

退出码：0 = 可以上传，1 = 发现风险，请先处理。
"""

import re
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

ROOT = Path(__file__).resolve().parent.parent

# 必须被 .gitignore 排除的敏感路径
SENSITIVE_PATHS = [
    ".env",
    "api/.env",
    ".venv",
    "tools",
    "static",
    "xwzx-news/node_modules",
    "xwzx-news/dist",
]

# 绝不允许出现在「即将提交内容」中的模式
HARD_PATTERNS = {
    "真实 API 密钥": r"sk-[A-Za-z0-9]{16,}",
    "AWS Access Key": r"AKIA[0-9A-Z]{16}",
    "GitHub Token": r"gh[pousr]_[A-Za-z0-9]{20,}",
    "Google API Key": r"AIza[0-9A-Za-z_-]{30,}",
    "Slack Token": r"xox[baprs]-[A-Za-z0-9-]{10,}",
    "私钥文件内容": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
}

# 允许出现在文档/示例文件中的模式（仅提示）
SOFT_PATTERNS = {
    "示例数据库连接串": r"(mysql|postgresql|mongodb|redis)(\+\w+)?://[^:\s/]+:[^@\s]{3,}@",
}

# 这些文件属于「说明性文件」，其中的示例值不算泄露
DOC_SUFFIXES = (".md", ".example", ".txt", ".bat")

PASSED = 0
FAILED = 0
WARNED = 0


def check(name: str, ok: bool, detail: str = ""):
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  [PASS] {name}")
    else:
        FAILED += 1
        print(f"  [FAIL] {name}")
        for line in detail.splitlines():
            if line:
                print(f"         {line}")


def warn(name: str, detail: str = ""):
    global WARNED
    WARNED += 1
    print(f"  [提示] {name}")
    for line in detail.splitlines():
        if line:
            print(f"         {line}")


def run_git(*args: str) -> tuple[int, str]:
    try:
        r = subprocess.run(
            ["git", *args], cwd=str(ROOT), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=60,
        )
        return r.returncode, (r.stdout or "")
    except Exception:  # noqa: BLE001
        return 127, ""


def is_doc(path: str) -> bool:
    p = path.lower()
    return p.endswith(DOC_SUFFIXES) or Path(p).name.startswith(".env")


def read_gitignore_patterns() -> list[str]:
    p = ROOT / ".gitignore"
    if not p.exists():
        return []
    return [
        line.strip() for line in p.read_text(encoding="utf-8", errors="ignore").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def matches_gitignore(path: str, patterns: list[str]) -> bool:
    """用 .gitignore 的规则粗判路径是否会被忽略（没有 git 时的降级检查）。

    按从先到后的顺序累积判断，支持 `!` 取反（与 git 的语义一致）。
    """
    path = path.replace("\\", "/")
    name = Path(path).name
    ignored = False

    def hit(pat: str, target: str) -> bool:
        # gitignore 的 `*` 不跨目录，所以用正则逐段匹配，而不是 fnmatch
        regex = re.escape(target).replace(r"\*", "[^/]*").replace(r"\?", "[^/]")
        return re.fullmatch(regex, path) is not None

    for raw in patterns:
        negate = raw.startswith("!")
        pat = raw.lstrip("!").strip()
        if not pat:
            continue

        is_dir = pat.endswith("/")
        target = pat.rstrip("/")
        matched = False

        if is_dir:
            # 目录规则：路径本身等于该目录，或位于该目录之下
            matched = (
                path == target
                or path.startswith(target + "/")
                or f"/{target}/" in f"/{path}/"
            )
        else:
            # 文件规则：匹配任意层级的同名文件/目录，或按完整路径匹配
            matched = (
                path == target
                or name == target
                or path.startswith(target + "/")
                or hit(pat, target)
            )

        if matched:
            ignored = not negate

    return ignored


def get_commit_files() -> tuple[list[str], str]:
    """返回 (文件清单, 来源说明)。优先用 git，退化到工作区扫描。"""
    code, out = run_git("add", "--dry-run", ".")
    if code == 0:
        files = [
            line.strip()[5:-1]
            for line in out.splitlines()
            if line.strip().startswith("add '") and line.strip().endswith("'")
        ]
        if files:
            return files, "git 索引"

    # 没有 git：按 .gitignore 规则模拟
    patterns = read_gitignore_patterns()
    files = []
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        if any(part in {".git", "__pycache__"} for part in p.parts):
            continue
        if matches_gitignore(rel, patterns):
            continue
        files.append(rel)
    return files, "按 .gitignore 模拟"


def main():
    print("=" * 64)
    print("上传 GitHub 前的安全自检")
    print("=" * 64)

    code, _ = run_git("rev-parse", "--is-inside-work-tree")
    has_git = code == 0
    print(f"git 仓库: {'是' if has_git else '否（将按 .gitignore 规则模拟）'}")

    # ------------------------------------------------------------------
    print("\n[1] 敏感路径是否被排除")
    # ------------------------------------------------------------------
    patterns = read_gitignore_patterns()
    check(".gitignore 存在", (ROOT / ".gitignore").exists())

    for path in SENSITIVE_PATHS:
        if not (ROOT / path).exists():
            print(f"  [跳过] {path}（本地不存在）")
            continue
        if has_git:
            rc, _ = run_git("check-ignore", "-q", "--", path)
            ignored = rc == 0
        else:
            ignored = matches_gitignore(path, patterns)
        check(f"{path} 不会被提交", ignored, "该路径会被提交到仓库！")

    # ------------------------------------------------------------------
    print("\n[2] 即将提交的文件清单")
    # ------------------------------------------------------------------
    files, source = get_commit_files()
    print(f"  来源: {source}，共 {len(files)} 个文件")

    env_leaked = [f for f in files if Path(f).name == ".env"]
    check("清单中没有 .env 文件", not env_leaked, "\n".join(env_leaked))

    big = [
        f"{f}（{(ROOT / f).stat().st_size / 1024 / 1024:.1f} MB）"
        for f in files
        if (ROOT / f).is_file() and (ROOT / f).stat().st_size > 5 * 1024 * 1024
    ]
    check("没有单个文件超过 5 MB", not big, "\n".join(big))

    # ------------------------------------------------------------------
    print("\n[3] 即将提交内容中的密钥扫描")
    # ------------------------------------------------------------------
    binary_ext = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".woff", ".woff2", ".exe", ".pdb", ".svg"}
    texts: dict[str, str] = {}
    for f in files:
        p = ROOT / f
        if not p.is_file() or p.suffix.lower() in binary_ext:
            continue
        try:
            texts[f] = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:  # noqa: BLE001
            continue

    for label, pattern in HARD_PATTERNS.items():
        compiled = re.compile(pattern)
        hits = []
        for f, text in texts.items():
            for lineno, line in enumerate(text.splitlines(), 1):
                m = compiled.search(line)
                if not m:
                    continue
                # 文档里的示例密钥（全是 x 或明显占位）只提示
                token = m.group(0)
                body = token[3:]
                placeholder = set(body.lower()) <= {"x", "*", "0"} or "填写" in line
                hits.append((f, lineno, line.strip()[:90], placeholder))

        real = [h for h in hits if not h[3]]
        fake = [h for h in hits if h[3]]

        if real:
            check(
                f"{label}：无真实密钥",
                False,
                "\n".join(f"{f}:{n}  {t}" for f, n, t, _ in real[:10]),
            )
        else:
            print(f"  [PASS] {label}：无真实密钥")
        for f, n, t, _ in fake[:3]:
            warn(f"{label}：文档中的示例值（非真实密钥）", f"{f}:{n}  {t}")

    for label, pattern in SOFT_PATTERNS.items():
        compiled = re.compile(pattern)
        doc_hits, code_hits = [], []
        for f, text in texts.items():
            for lineno, line in enumerate(text.splitlines(), 1):
                if compiled.search(line):
                    (doc_hits if is_doc(f) else code_hits).append(f"{f}:{lineno}  {line.strip()[:90]}")

        if code_hits:
            check(
                f"{label}：代码文件中无硬编码凭据",
                False,
                "\n".join(code_hits[:10]),
            )
        else:
            print(f"  [PASS] {label}：代码文件中无硬编码凭据")
        for h in doc_hits[:5]:
            warn(f"{label}：文档/示例中的示意值", h)

    # ------------------------------------------------------------------
    print("\n[4] .env.example 只含占位符")
    # ------------------------------------------------------------------
    for example in [".env.example", "api/.env.example", "xwzx-news/.env.example"]:
        p = ROOT / example
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        real_key = re.search(r"sk-[A-Za-z0-9]{16,}", text)
        check(f"{example} 无真实密钥", real_key is None,
              f"发现：{real_key.group(0) if real_key else ''}")

    # ------------------------------------------------------------------
    print("\n" + "=" * 64)
    print(f"结果：{PASSED} 项通过，{FAILED} 项失败，{WARNED} 项提示")
    if FAILED == 0:
        print("✅ 自动化安全检查通过，可以上传。")
        print()
        print("⚠️  以下两点脚本无法判断，请人工确认：")
        print("   1. 曾经以明文形式存在过的密钥，是否已到服务商控制台吊销并重置？")
        print("      吊销后旧密钥无论出现在哪里都失效，这是唯一彻底的补救方式。")
        print("   2. 仓库里是否还有不该公开的业务数据（真实用户信息、内部文档等）？")
    else:
        print("❌ 发现风险，请先处理后再上传。")
    print("=" * 64)

    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
