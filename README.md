# Skills 目录

该目录下的 Skill 供 Claude Code 按需调用。

## create-pyi

为 Python 模块生成一对文件：`module.pyi`（类型存根）和 `module.py`（去注解的源文件）。

- **`.pyi`**：完整类型注解 + 文档字符串 + 展开的 `@overload` 重载签名，方法体用 `...` 占位
- **`.py`**：移除类型注解和 `@overload` 变体，保留所有实现代码
- `@overload` 变体全部保留并展开；`@abstractmethod` 省略；`@final`/`@property` 等保留
- 文档字符串内容规则依赖 **write-docstring** Skill

详见 [create-pyi/SKILL.md](./create-pyi/SKILL.md) 及同级 `overload规则.md`。

## write-docstring

为 Python 代码（尤其是 `.pyi` 存根文件）的公共接口生成符合规范的文档字符串。

- 文档由独立组件按需组合：功能简述 + 详细说明 + `:param` + `:return` + `:raises` + `Example` + `Note`
- 不同接口类型（类、属性、模块级变量、`@overload`）选取不同组件组合
- 标准行为的魔术方法省略文档，特殊逻辑才需文档
- 中文排版规范：中英文/中文数字间空格、半角括号

详见 [write-docstring/SKILL.md](./write-docstring/SKILL.md) 及同级 `@overload文档规则.md`。

## commit

分析 Git 已暂存变更并生成 Conventional Commits 格式的提交信息或执行代码审查。

- 自动检测暂存变更并推断 type、scope，生成标准格式提交信息
- 支持两阶段代码审查（机械预检 + AI 审查），覆盖安全、逻辑、完整性等维度
- Ruff 安全规则扫描 + 自定义正则检测，规则由 `review_config.yaml` 配置驱动
- 审查发现问题后询问用户是否插入 `TODO))` 标记并随代码入库

详见 [commit/SKILL.md](./commit/SKILL.md) 及同级 `审查规则.md`。

## create-skill

创建、重构或拆分 Claude Code Skill 定义。

- 设计 SKILL.md 的结构化元数据（name、description、version）
- 定义核心任务、使用方式、执行流程、检查清单
- 支持将现有 Skill 拆分为多个或合并多个 Skill

详见 [create-skill/SKILL.md](./create-skill/SKILL.md)。
