"""对 Git 已暂存变更中的 Python 代码执行机械预检.

基于 Ruff, 从 review_config.yaml 读取配置.
输出报告到终端, 可选 --json 输出供 annotate.py 使用.
退出码: 0 = 无阻断性问题, 1 = 存在 error/critical 问题.
"""

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath

import yaml


@dataclass
class Finding:
    lineno: int
    level: str
    category: str
    description: str
    filepath: str = ""


_CONFIG_DIR = Path(__file__).parent
_CONFIG_PATH = _CONFIG_DIR / "review_config.yaml"
_RUFF_TOML = _CONFIG_DIR / "ruff.toml"
_BLOCKING = {"error", "critical"}


def _load_config() -> dict:
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def _get_staged_diff() -> str:
    result = subprocess.run(
        ["git", "diff", "--cached", "-U0"], capture_output=True, text=True, encoding="utf-8", check=True, )
    return result.stdout


def _parse_diff(diff: str) -> dict[str, list[tuple[int, str]]]:
    files: dict[str, list[tuple[int, str]]] = {}
    current: str | None = None
    offset = 0
    new_start = 0
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
        elif line.startswith('+++ "b/'):
            current = line[7:].rstrip('"')
        elif line.startswith("+++ "):
            continue
        elif line.startswith("@@ "):
            m = re.search(r"\+(\d+)(?:,(\d+))?", line)
            if m:
                new_start = int(m.group(1))
                offset = 0
        elif line.startswith("+") and current:
            files.setdefault(current, []).append((new_start + offset, line[1:]))
            offset += 1
        elif line.startswith(" ") and current:
            offset += 1
    return files


def _run_ruff(filepath: str) -> list[dict]:
    """执行 Ruff 检查, 返回原始 issue 列表. 出错时返回空列表."""
    args = [
        "ruff", "check", "--output-format", "json", "--no-cache", "--config", str(_RUFF_TOML), filepath,
    ]
    result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
    if result.returncode == 2:
        print(f"ruff 运行出错: {filepath}\n{result.stderr}", file=sys.stderr)
        return []
    try:
        return json.loads(result.stdout) if result.stdout.strip() else []
    except json.JSONDecodeError:
        return []


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="代码机械预检")
    parser.add_argument("--json", help="将发现结果写到 JSON 文件")
    args = parser.parse_args()

    diff = _get_staged_diff()
    if not diff:
        print("没有检测到已暂存的变更")
        return 0

    config = _load_config()
    ignore_patterns = config.get("ignore", [])
    severity_overrides = config.get("severity_overrides", {})
    file_types = config.get("file_types", [".py"])
    ruff_cfg = config.get("ruff", {})
    ruff_ok = ruff_cfg.get("enabled", True)

    if ruff_ok:
        try:
            subprocess.run(["ruff", "--version"], capture_output=True, check=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            ruff_ok = False

    changed_files = _parse_diff(diff)
    all_findings: list[Finding] = []
    has_blocking = False

    for filepath, file_lines in changed_files.items():
        if not any(filepath.endswith(ft) for ft in file_types):
            continue

        posix_path = PurePosixPath(filepath.replace("\\", "/"))
        if any(posix_path.match(p) for p in ignore_patterns):
            continue

        staged_lines = {lineno for lineno, _ in file_lines}
        findings: list[Finding] = []

        if ruff_ok:
            for issue in _run_ruff(filepath):
                code = issue.get("code", "")
                lineno = issue.get("location", {}).get("row", 0)
                if lineno not in staged_lines:
                    continue

                level = severity_overrides.get(code, "critical" if code.startswith("T") else "error")
                if code.startswith("T"):
                    cat = "调试残留"
                elif code.startswith("S10"):
                    cat = "敏感信息"
                elif code.startswith("S"):
                    cat = "不安全代码"
                else:
                    cat = "代码质量"

                findings.append(
                    Finding(
                        lineno=lineno,
                        level=level,
                        category=cat,
                        filepath=filepath,
                        description=issue.get("message", ""), ))

        if not findings:
            continue

        all_findings.extend(findings)
        for f in findings:
            print(f"{filepath}:{f.lineno}:{f.level}: {f.category}: {f.description}")
            if f.level in _BLOCKING:
                has_blocking = True

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump([asdict(fi) for fi in all_findings], f, ensure_ascii=False, indent=2)

    if not all_findings:
        print("审查通过, 未发现问题")

    return 1 if has_blocking else 0


if __name__ == "__main__":
    sys.exit(main())
