# @overload 重载规则

仅通过 `create-pyi/SKILL.md` 引用, 不单独使用。

---

## 实现签名规则

**始终保留实现签名。** 不判断"变体是否已覆盖"，避免误判导致遗漏。

```python
from typing import overload

@overload
def func(x: int) -> str: ...
@overload
def func(x: str) -> str: ...

def func(x: int | str) -> str: ...
```

即使变体看似覆盖了全部输入，也保留实现签名。这是避免遗漏的最安全策略。

---

## 重载布局

所有 `@overload` 变体后跟实现签名：

```python
from typing import overload

@overload
def func(x: int) -> str: ...
@overload
def func(x: float) -> int: ...

def func(x: int | float) -> str | int: ...
```

每个 `@overload` 变体独占一个代码块, `@overload` 上方空一行与上一个变体分隔。

### 魔术方法

```python
from typing import overload

@overload
def __getitem__(self, index: int) -> str: ...
@overload
def __getitem__(self, index: slice) -> list[str]: ...

def __getitem__(self, index: int | slice) -> str | list[str]: ...
```

### 类方法

`@overload` 在 `@classmethod` 上方。

```python
from typing import overload

@overload
@classmethod
def func(cls, x: str) -> int: ...
@overload
@classmethod
def func(cls, x: dict[str, Any]) -> str: ...

@classmethod
def func(cls, x: str | dict[str, Any]) -> int | str: ...
```

---

## 源码 `typing.overload` 的处理

```python
# 源码
import typing

@typing.overload
def func(x: int) -> str: ...

# .pyi 输出
from typing import overload

@overload
def func(x: int) -> str: ...
```

---

## 质量检查清单

- [ ] `@overload` 重载函数的所有变体均已展开列出
- [ ] 始终保留了实现签名
- [ ] 导入了 `overload` (如有重载函数)
- [ ] 源码中的 `typing.overload` 已转为 `from typing import overload`
