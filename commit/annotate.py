"""在源文件中插入 TODO 标记注释.

从机械预检(--mech)和 AI 审查(--ai)的 JSON 中合并发现,
在问题行上方写入 TODO 标记, 随代码入库.

用法:
  python annotate.py --mech findings.json --ai ai_findings.json
  python annotate.py --mech findings.json   # 仅机械发现
"""

import argparse
import json
import sys
from pathlib import Path

_COMMENT_LANG = {".py": "#"}


def _tag(filepath: str, finding: dict) -> str:
    prefix = _COMMENT_LANG.get(Path(filepath).suffix, "#")
    return (
        f"{prefix} TODO)) [{finding['level']}] "
        f"@review {finding['category']}: {finding['description']}"
    )


def _annotate_file(filepath: str, findings: list[dict]):
    path = Path(filepath)
    if not path.exists():
        return

    lines = path.read_text(encoding="utf-8").splitlines()
    for f in sorted(findings, key=lambda x: x["lineno"], reverse=True):
        idx = f["lineno"] - 1
        if idx > 0 and "TODO))" in lines[idx - 1]:
            continue  # 避免重复标注
        lines.insert(idx, _tag(filepath, f))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="插入 TODO 审查标记")
    parser.add_argument("--mech", required=True, help="机械预检结果 JSON")
    parser.add_argument("--ai", help="AI 审查结果 JSON (可选)")
    args = parser.parse_args()

    all_items: list[dict] = []
    for path in [args.mech, args.ai]:
        if not path:
            continue
        with open(path, encoding="utf-8") as f:
            all_items.extend(json.load(f))

    if not all_items:
        print("没有发现要标记的问题")
        return 0

    by_file: dict[str, list[dict]] = {}
    for item in all_items:
        if item["lineno"] == 0:
            continue  # 跳过非行级问题
        by_file.setdefault(item["filepath"], []).append(item)

    for filepath, items in by_file.items():
        _annotate_file(filepath, items)
        print(f"已标记 {filepath}: {len(items)} 处")

    return 0


if __name__ == "__main__":
    sys.exit(main())
