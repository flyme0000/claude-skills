"""对 Git 已暂存变更执行代码审查.

在检测到问题的代码行上方插入 TODO)) [级别] @review 标记注释。
退出码: 0 = 无阻断性问题, 1 = 存在 error/critical 问题。
"""

import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

# 检测规则: (正则, 级别, 分类, 描述模板)
_SQL_KEYWORDS = r'\b(?:select|insert|update|delete|drop|alter|create)\b'
_PATTERNS: list[tuple[re.Pattern, str, str, str]] = [
    # error — 确定有问题
    (
        re.compile(r'\b(eval|exec)\s*\('),
        'error', '不安全代码', '{0}() 调用',
    ),
    (
        re.compile(
            r"""f['"].*""" + _SQL_KEYWORDS + r""".*\{""", re.I),
        'error', '不安全代码', 'SQL 注入风险 (f-string)',
    ),
    (
        re.compile(
            r"""['"].*""" + _SQL_KEYWORDS + r""".*['"]\s*[+%]""", re.I),
        'error', '不安全代码', 'SQL 注入风险 (拼接)',
    ),
    (
        re.compile(r'\bverify\s*=\s*[Ff]alse\b'),
        'error', '不安全代码', 'verify=False 跳过证书验证',
    ),
    (
        re.compile(
            r"""\b(?:api_key|password|secret|token)\s*[=:]\s*['"][^'"]{4,}['"]""",
            re.I),
        'error', '敏感信息', '疑似 {0} 硬编码',
    ),

    # critical — 高度可疑
    (
        re.compile(r'^\s*print\s*\('),
        'critical', '调试残留', 'print() 调用',
    ),
    (
        re.compile(r'\bpdb\.set_trace\s*\('),
        'critical', '调试残留', 'pdb.set_trace() 断点',
    ),
    (
        re.compile(r'\bconsole\.log\s*\('),
        'critical', '调试残留', 'console.log() 调用',
    ),
    (
        re.compile(r'\bdebugger\b'),
        'critical', '调试残留', 'debugger 语句',
    ),
    (
        re.compile(r'\bshell\s*=\s*True\b'),
        'critical', '不安全代码', 'shell=True 命令注入风险',
    ),
    (
        re.compile(r'\bpickle\.(?:load|loads)\s*\('),
        'critical', '不安全代码', 'pickle 反序列化风险',
    ),
    (
        re.compile(r'\byaml\.load\s*\('),
        'critical', '不安全代码', 'yaml.load() 缺少 SafeLoader',
    ),

    # warning — 潜在隐患
    (
        re.compile(r'\btime\.sleep\s*\('),
        'warning', '阻塞调用', 'time.sleep() 固定延时',
    ),
    (
        re.compile(r'\bsubprocess\.(?:Popen|run)\s*\('),
        'warning', '子进程调用', 'subprocess 调用',
    ),
    (
        re.compile(r'\bos\.system\s*\('),
        'critical', '子进程调用', 'os.system 调用',
    ),

    # info — 仅供参考
    (
        re.compile(r'\b(TODO|FIXME|XXX|HACK)\b'),
        'info', '待办标记', '{0}',
    ),
]

_SEVERITY_ORDER = {'error': 0, 'critical': 1, 'warning': 2, 'info': 3}
_BLOCKING = {'error', 'critical'}


def _get_staged_diff() -> str:
    """获取 git 已暂存变更的 diff 输出."""
    result = subprocess.run(
        ['git', 'diff', '--cached', '-U0'],
        capture_output=True, text=True, encoding='utf-8', check=True,
    )
    return result.stdout


def _parse_diff(diff: str) -> dict[str, list[tuple[int, str]]]:
    """解析 diff 为 {文件路径: [(新文件行号, 行内容), ...]}."""
    files: dict[str, list[tuple[int, str]]] = defaultdict(list)
    current: str | None = None
    offset = 0
    new_start = 0

    for line in diff.splitlines():
        if line.startswith('+++ b/'):
            current = line[6:]
        elif line.startswith('+++ "b/'):
            current = line[7:].rstrip('"')
        elif line.startswith('@@ '):
            m = re.search(r'\+(\d+)(?:,(\d+))?', line)
            if m:
                new_start = int(m.group(1))
                offset = 0
        elif line.startswith('+') and current:
            files[current].append((new_start + offset, line[1:]))
            offset += 1
        elif line.startswith(' ') and current:
            offset += 1

    return files


def _detect(line: str) -> tuple[str, str, str] | None:
    """对单行内容匹配所有规则, 返回最严重的一条结果 (级别, 分类, 描述) 或 None."""
    best = None
    best_order = 999
    for regex, level, category, desc_tmpl in _PATTERNS:
        m = regex.search(line)
        if m:
            order = _SEVERITY_ORDER[level]
            if order < best_order:
                groups = m.groups() or (m.group(0),)
                best = (level, category, desc_tmpl.format(*groups))
                best_order = order
    return best


def _comment_prefix(filepath: str) -> str:
    """根据文件扩展名返回注释符号前缀."""
    ext = Path(filepath).suffix
    fmt = {
        '.py': '#',
        '.js': '//',
        '.ts': '//',
        '.jsx': '//',
        '.tsx': '//',
        '.go': '//',
        '.rs': '//',
        '.java': '//',
        '.c': '//',
        '.cpp': '//',
        '.h': '//',
        '.hpp': '//',
        '.sh': '#',
        '.yaml': '#',
        '.yml': '#',
        '.toml': '#',
        '.ini': ';',
        '.vue': '<!--',
        '.html': '<!--',
        '.md': '<!--',
    }.get(ext, '#')
    return fmt


def _annotate_file(filepath: str, findings: list[tuple[int, str, str, str]]):
    """在源文件对应行上方插入 TODO)) 标记注释."""
    path = Path(filepath)
    if not path.exists():
        return

    prefix = _comment_prefix(filepath)
    close = ' -->' if prefix == '<!--' else ''
    tag_fmt = f"{prefix} TODO)) [{{level}}] @review {{category}}: {{desc}}{close}"

    lines = path.read_text(encoding='utf-8').splitlines()
    # 从下往上处理, 避免上行插入影响后续行号
    for entry in sorted(findings, key=lambda x: x[0], reverse=True):
        lineno, level, category, desc = entry
        tag = tag_fmt.format(level=level, category=category, desc=desc)
        lines.insert(lineno - 1, tag)
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main() -> int:
    diff = _get_staged_diff()
    if not diff:
        print('没有检测到已暂存的变更')
        return 0

    files = _parse_diff(diff)
    has_blocking = False
    total = 0

    for filepath, file_lines in files.items():
        findings: list[tuple[int, str, str, str]] = []
        for lineno, line in file_lines:
            result = _detect(line)
            if result:
                level, category, desc = result
                findings.append((lineno, level, category, desc))
                print(f'{filepath}:{lineno}:{level}: {category}: {desc}')
                total += 1
                if level in _BLOCKING:
                    has_blocking = True

        if findings:
            _annotate_file(filepath, findings)

    if total == 0:
        print('审查通过，未发现问题')

    return 1 if has_blocking else 0


if __name__ == '__main__':
    sys.exit(main())
