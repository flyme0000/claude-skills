# @overload 文档规则

仅通过 `文档注释生成/SKILL.md` 引用, 不单独使用。

---

## 核心规则

各变体描述自身的特殊性, 最终实现涵盖共性。

## 文档分布规则

文档组件在 `@overload` 变体和最终实现签名之间的分布如下:

| 文档组件 | 各 `@overload` 变体 | 最终实现签名 |
|----------|--------------------|-------------|
| 功能简述 | 该变体特有的简述 | — (不需要) |
| 详细说明 | — | 整体行为说明 |
| `:param` | 该变体特有的参数 | — (不需要) |
| `:return` | 该变体特有的返回值 | — (不需要) |
| `:raises` | 该变体特有的异常 | 所有变体共有的异常 |
| `Example` | — | 各变体的使用示例 |
| `Note` | — | 注意事项 |

## 完整布局参考

以下汇集了所有文档组件的布局, 供参考格式:

```python
@overload
def func(x: int) -> str:
    """
    整数输入处理.

    :param x: 整数输入
    :return: 字符串格式结果
    """

@overload
def func(x: float) -> int:
    """
    浮点数输入处理.

    :param x: 浮点数输入
    :return: 四舍五入后的整数结果
    """

def func(x: int | float) -> str | int:
    """
    处理输入并返回结果.

    支持整数和浮点数两种输入形式.

    :raises TypeError: 输入类型不支持时抛出

    Example::
        func(42)
        func(3.14)
    """
    ...
```

## 功能简述的分布

每个变体描述自己的行为, 最终实现不需要重复功能简述。

```python
@overload
def func(x: int) -> str:
    """将整数格式化为字符串."""

@overload
def func(x: float) -> int:
    """将浮点数取整."""

def func(x: int | float) -> str | int:
    ...
```

如果一个变体的行为无法用一句话概括, 和详细说明合并在同一个文档块中:

```python
@overload
def func(x: int) -> str:
    """
    将整数格式化为字符串.

    使用指定的进制和字母大小写规则进行转换.
    """
```

## :param 和 :return 的分布

各变体独有的参数和返回值写在该变体上, 最终实现不重复。

```python
@overload
def func(x: int, base: int = 10) -> str:
    """
    整数转字符串.

    :param x: 待转换的整数
    :param base: 进制, 默认为 10
    :return: 转换后的字符串
    """

@overload
def func(x: float, decimals: int = 0) -> str:
    """
    浮点数格式化.

    :param x: 待格式化的浮点数
    :param decimals: 小数位数, 默认为 0
    :return: 格式化后的字符串
    """

def func(x: int | float, **kwargs: int) -> str:
    """
    将数值转为字符串.

    :raises ValueError: 参数无效时抛出
    """
    ...
```

如果各变体的参数名和类型不同, 最终实现的参数注解使用联合类型覆盖所有变体。最终实现上的 `:param` 只需要写联合参数的含义, 变体已覆盖的不重复。

## :raises 的分布

变体特有的 `:raises` 写在变体上, 所有变体共有的写在最终实现上。

```python
@overload
def func(x: int) -> str:
    """
    处理整数.

    :param x: 整数输入
    :return: 字符串结果
    :raises OverflowError: 数值超出范围时抛出
    """

@overload
def func(x: float) -> str:
    """
    处理浮点数.

    :param x: 浮点数输入
    :return: 字符串结果
    :raises OverflowError: 数值超出范围时抛出
    """

def func(x: int | float) -> str:
    """
    处理输入.

    :raises TypeError: 输入类型不支持时抛出

    Example::
        func(42)
    """
    ...
```

## Example 和 Note 的分布

使用示例和注意事项放在最终实现上, 展示各变体的用法。

```python
@overload
def func(x: int) -> str: ...

@overload
def func(x: float) -> int: ...

def func(x: int | float) -> str | int:
    """
    处理输入并返回结果.

    Example::
        func(42)
        func(3.14)

    Note:
        输入超出范围时会引发 OverflowError.
    """
    ...
```

---

## 质量检查清单

- [ ] `@overload` 的各变体包含了变体特有的 `:param`, `:return`, `:raises` 和功能简述
- [ ] `@overload` 的最终实现上只保留了共性文档 (`:raises`, `Example`, `Note`, 整体说明)
- [ ] `@overload` 的最终实现上未重复变体已覆盖的 `:param` 和 `:return`
- [ ] 各变体描述了自身的特殊性, 最终实现涵盖共性
