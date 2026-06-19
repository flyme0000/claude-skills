---
name: 存根文件编写
description: 当用户要求生成 Python .pyi 类型存根文件、编写类型注解文件、生成 .pyi 和 .py 配对文件、编写 Python 模块的类型存根、需要 stub 文件时使用此 Skill。也适用于用户提供 Python 代码要求生成对应的类型存根和精简实现文件。
version: 1.3.0
---

# 存根文件编写 Skill

## 核心任务

根据用户提供的 Python 模块代码, 生成一对文件:

1. **module.pyi** — 类型存根文件: 完整类型注解、文档字符串、展开的 `@overload` 重载签名
2. **module.py** — 源文件的轻量变换版本: 移除类型注解和 `@overload` 变体, **保留所有实现代码**

`.pyi` 中文档字符串的**内容**规则参见 **文档注释生成** Skill。

## 文件结构

```
project/
├── module.py          # 输出去注解版本 (保留实现)
└── module.pyi         # 输出版存根 (完整类型注解)
```

---

## 模块级设置

### 导入声明
- 保留必要导入如 `from abc import ABCMeta`, `from typing import ...`
- 若源码使用了 `@overload`, 在 `.pyi` 中添加 `from typing import overload`
- 若源码使用 `typing.overload` (通过 `import typing`), 转为 `from typing import overload`
- **不导入** `abstractmethod`

### 类型注解
- 所有公共接口必须包含完整的类型注解
- 泛型类型变量正确定义: `T = TypeVar('T', bound=BaseType)`
- 类型别名正确声明: `TypeAlias = Callable[[T], None]`
- 私有函数 (以 `_` 开头) 视情况添加合理注解

### 方法实现占位
- 使用 `...` (Ellipsis) 代替所有方法/函数体
- 不使用 `pass` 或 `raise NotImplementedError`

### 装饰器处理

| 装饰器 | .pyi | .py |
|--------|------|-----|
| `@final`, `@property`, `@classmethod`, `@staticmethod` | 保留 | 保留 |
| `@overload` | 保留并展开 | 移除 |
| `@abstractmethod` | 省略 | 保留 |

---

## @overload 重载处理

**必须**同时读取本目录下的 `overload规则.md`。

`@overload` 在 `.pyi` 和 `.py` 之间的处理差异:

| 方面 | .pyi | .py |
|------|------|-----|
| `@overload` 变体 | 全部保留并展开 | 全部移除 |
| 实现签名 | 变体覆盖所有情况时省略, 否则保留 | 保留 (保持源文件原样) |
| 实现体 | `...` (Ellipsis) | 保留源文件实现 |
| `overload` 导入 | 添加 `from typing import overload` | 不添加 |

---

## .py 生成规则

### 核心原则

对源文件做两件事:
1. 移除所有类型注解
2. 移除所有 `@overload` 变体

**其余代码保持源文件原样。** 包括函数体、异常处理、条件分支、循环、赋值、函数调用等全部实现代码。

### 移除项

| 目标 | 操作 | 示例 |
|------|------|------|
| 函数参数注解 | 删除 `: 类型` | `def func(x: int, y: str)` → `def func(x, y)` |
| 函数返回值注解 | 删除 `-> 类型` | `def func() -> int:` → `def func():` |
| 变量类型注解 | 删除 `: 类型` | `x: int = 5` → `x = 5` |

### 保留项

- **全部实现代码**: 函数体、异常处理、条件分支、循环、赋值、函数调用等
- 所有装饰器: `@abstractmethod`, `@property`, `@classmethod`, `@staticmethod`
- 行注释和块注释
- 导入语句
- 模块级变量及其初始化逻辑

### 文档字符串

当 `.pyi` 中某函数/类的文档字符串包含 `:param`、`:return` 或超过一句话时, 判定为"详细文档", `.py` 的对应位置生成一句话功能简述。否则 `.py` 保持源文件原样。

一句话简述的来源:
1. 源文件已有文档字符串 → 取其第一句
2. 源文件无文档字符串 → 生成 "功能简述."

```python
# .pyi 输出 (包含详细文档)
async def func(x: int) -> None:
    """
    功能简述.

    详细说明行为和使用场景.

    :param x: 参数说明
    """
    ...

# .py 输出 (保留实现 + 一句话简述)
async def func(x):
    """功能简述."""
    # <源代码的完整实现体>
```

```python
# .pyi 中无详细文档 (标准魔术方法)
@final
def __hash__(self) -> int: ...

# .py 保持源文件原样 (包括原有文档)
@final
def __hash__(self):
    return id(self)
```

### 类型注解移除示例

```python
# 源码 / .pyi 输出
def func(x: int, flag: bool = False) -> str:
    """功能简述."""
    if isinstance(x, int):
        return str(x)
    return round(x)

# .py 输出
def func(x, flag=False):
    """功能简述."""
    if isinstance(x, int):
        return str(x)
    return round(x)
```

### @overload 变体移除示例

```python
# 源码 / .pyi 输出
from typing import overload

@overload
def func(x: int) -> str: ...

@overload
def func(x: float) -> int: ...

def func(x: int | float) -> str | int:
    """功能简述."""
    return str(x) if isinstance(x, int) else round(x)

# .py 输出 (移除 overload 变体, 保留实现)
def func(x):
    """功能简述."""
    return str(x) if isinstance(x, int) else round(x)
```

### 注意事项

- 删除参数注解时保留默认值: `x: int = 5` → `x = 5`
- 删除变量注解时区分赋值语句: `x: int = 5` → `x = 5`
- 参数名与 `.pyi` 保持完全一致
- 不调整缩进、空行、空格等代码格式

---

## 输出格式

对于每个输入模块, 按以下顺序输出:
1. **module.pyi** — 完整的存根文件
2. **module.py** — 去掉类型注解和 `@overload` 变体的源文件

---

## 已有存根的更新

当源文件相对于已有输出文件发生变更时, **按需**读取本目录下的 `已有存根更新规则.md`。

---

## 质量检查清单

### .pyi 文件
- [ ] 所有公共接口都有类型注解
- [ ] 使用 `...` 代替方法实现
- [ ] 省略 `@abstractmethod` 装饰器
- [ ] 保留 `@final`, `@property` 等装饰器
- [ ] `@overload` 重载函数的所有变体均已展开列出
- [ ] 导入了 `overload` (如有重载函数)
- [ ] 变体已覆盖所有调用情况时省略了实现签名
- [ ] 存在未覆盖调用情况时保留了实现签名

### .py 文件
- [ ] 不包含任何类型注解
- [ ] 已移除所有 `@overload` 变体
- [ ] 实现代码保持源文件原样, 未被替换为 NotImplementedError
- [ ] 装饰器保持源文件原样
- [ ] 行注释和块注释保持源文件原样
- [ ] 导入语句保持源文件原样
- [ ] 参数名与 `.pyi` 完全一致
- [ ] 对应于 `.pyi` 有详细文档的位置, 生成了功能简述
- [ ] 对应于 `.pyi` 无详细文档的位置, 文档保持源文件原样
