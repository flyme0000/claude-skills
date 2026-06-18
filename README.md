# Skills 目录

该目录下的 Skill 供 Claude Code 按需调用。

## 存根文件编写

为 Python 模块生成一对文件：`module.pyi`（类型存根）和 `module.py`（去注解的源文件）。

- **`.pyi`**：完整类型注解 + 文档字符串 + 展开的 `@overload` 重载签名，方法体用 `...` 占位
- **`.py`**：移除类型注解和 `@overload` 变体，保留所有实现代码
- `@overload` 变体全部保留并展开；`@abstractmethod` 省略；`@final`/`@property` 等保留
- 文档字符串内容规则依赖**文档注释生成** Skill

详见 [存根文件编写/SKILL.md](./存根文件编写/SKILL.md) 及同级 `overload规则.md`。

## 文档注释生成

为 Python 代码（尤其是 `.pyi` 存根文件）的公共接口生成符合规范的文档字符串。

- 文档由独立组件按需组合：功能简述 + 详细说明 + `:param` + `:return` + `:raises` + `Example` + `Note`
- 不同接口类型（类、属性、模块级变量、`@overload`）选取不同组件组合
- 标准行为的魔术方法省略文档，特殊逻辑才需文档
- 中文排版规范：中英文/中文数字间空格、半角括号

详见 [文档注释生成/SKILL.md](./文档注释生成/SKILL.md) 及同级 `@overload文档规则.md`。
