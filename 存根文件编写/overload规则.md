# @overload 重载规则

仅通过 `存根文件编写/SKILL.md` 引用, 不单独使用。

---

## 实现签名取舍

当所有有意义的调用组合都能被某个 `@overload` 变体匹配时, 省略。否则保留。

### 可省略: 变体已覆盖

```python
from typing import overload

@overload
def func(x: int) -> str: ...
@overload
def func(x: str) -> str: ...
```
`(int) → str` 和 `(str) → str` 覆盖了全部输入, 实现签名冗余。

### 不可省略: 存在未覆盖的组合

```python
from typing import overload

@overload
def func(x: int) -> str: ...
@overload
def func(x: float, flag: bool = False) -> int: ...

# func(42, True) 不匹配变体1 (无 flag)
# func(42, True) 不匹配变体2 (int ≠ float)
def func(x: int | float, flag: bool = False) -> str | int: ...
```

---

## 重载布局

### 精简布局 (变体已覆盖)

```python
from typing import overload

@overload
def func(x: int) -> str: ...
@overload
def func(x: float) -> int: ...
```

### 完整布局 (需保留实现签名)

```python
from typing import overload

@overload
def func(x: int) -> str: ...
@overload
def func(x: float) -> int: ...

def func(x: int | float) -> str | int: ...
```

每个 `@overload` 变体独占一个代码块, `@overload` 上方空一行与上一个变体分隔。

---

## 特殊方法重载

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
- [ ] 变体已覆盖所有调用情况时省略了实现签名
- [ ] 存在未覆盖调用情况时保留了实现签名
- [ ] 导入了 `overload` (如有重载函数)
- [ ] 源码中的 `typing.overload` 已转为 `from typing import overload`
