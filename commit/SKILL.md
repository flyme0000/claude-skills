---
name: commit
description: 分析 Git 已暂存变更并生成 Conventional Commit 格式的提交信息，供复制到 PyCharm Git GUI 中使用
version: 1.1.0
---

# 生成 Git 提交信息 Skill

## 核心任务

分析 Git 已暂存变更（对应 PyCharm Git GUI 中勾选的文件），生成 Conventional Commits 格式的提交信息，输出到终端供用户复制使用。
**不执行 git commit**。

## 变更检测规则

1. **只读取已暂存的变更**。执行 `git diff --cached` 获取差异，对应 PyCharm Git GUI 中勾选的文件。
2. **若无已暂存变更**，输出提示"没有检测到已暂存的变更"，终止流程。
3. 执行 `git diff --stat --cached` 获取变更文件概览，用于判断变更范围。

## 提交信息格式规则

提交信息必须严格按照以下格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

### type 选取规则

从下表选取**最精确匹配**的一个 type：

| type     | 含义  | 适用条件            |
|----------|-----|-----------------|
| feat     | 新功能 | 新增用户可见的特性、端点、能力 |
| fix      | 修复  | 修复了一个用户可见的 bug  |
| refactor | 重构  | 代码结构重组，不改变外部行为  |
| perf     | 性能  | 性能优化            |
| style    | 格式  | 代码格式调整，不改变语义    |
| test     | 测试  | 新增或修改测试代码       |
| docs     | 文档  | 仅文档、注释变更        |
| chore    | 杂务  | 构建、CI、依赖、配置变更   |
| revert   | 回滚  | 回滚之前的提交         |

若跨越多个 type，优先级：`feat > fix > refactor > perf > test > docs > style > chore`。

### scope 选取规则

1. **可选**。表示变更影响的主要模块或组件名，使用小写英文，单词间用连字符连接。
2. 从 diff 中变更文件最多的**一级子目录名**提取。例如 `src/`、`docs/`、`scripts/`。
3. 路径深度超过一层时只取**紧邻根的第一段**：`create-pyi/SKILL.md` → scope 取 `create-pyi`。
4. 跨越多个不同模块时不写 scope，在 body 中按目录分类列出影响范围。
5. 文件集中在项目根目录（如 `.gitignore`、`README.md`）时也不写 scope。

```python
# 变更集中在 docs/ 下 → scope: docs
# 变更分散在 api/、db/、ui/ → 不写 scope
# 变更集中在项目根目录 → 不写 scope
```

### subject 规则

1. 不超过 **72 个字符**
2. 使用**中文**描述
3. 祈使句格式，不加句号
4. 说明"做了什么"，不展开原因

### body 规则

1. **仅当 subject 不足以表达变更原因时使用**
2. 说明"为什么"，而非"做了什么"
3. 每行不超过 **72 个字符**
4. 多条原因用空行分隔

### footer 规则

1. **仅当有 Breaking Change 或关联 Issue 时使用**
2. Breaking Change 格式：`BREAKING CHANGE: <描述>`
3. 关联 Issue 格式：`Closes #<number>`

## 分析规则

1. **从文件名推断 type**：变更集中在 `test/` → `test`；`docs/` → `docs`；`.github/`、`setup.cfg` 等配置 → `chore`
2. **从 diff 内容推断 type**：新增错误处理 → `fix`；新增 API 端点 → `feat`；提取函数、重命名 → `refactor`
3. **关注变更意图**：相同代码改动在不同上下文中有不同 type
4. **多文件变更**：涉及 10 个以上文件时在 body 中按目录分类列出影响范围

## 代码审查模式

通过附加参数切换模式：

| 命令               | 行为                   |
|------------------|----------------------|
| `/commit`        | 生成提交信息（默认）           |
| `/commit review` | 审查已暂存变更，插入 REVIEW 标记 |
| `/commit both`   | 审查 + 生成提交信息          |

### 审查规则

**必须**同时读取本目录下的 **`审查规则.md`**。

使用本目录下的 `review.py` 执行审查：

```bash
python <skill-dir>/review.py
```

输出：每行一条 `文件路径:行号:级别: 分类: 描述` 格式的审查结果。
退出码：存在 error/critical 时返回 1，否则返回 0。

### 标记注释格式

命中后在源文件问题行上方插入：

```python
< !-- TODO)) [info] @ review
待办标记: TODO -->
# TODO)) [级别] @review 分类: 描述
```

标记**随代码入库**，进入版本控制。修复问题后由开发者手动删除。

### both 模式流程

1. 先执行 `review.py`
2. 若退出码为 1（存在 error/critical），**中断**，提示用户修复后重试
3. 若退出码为 0，继续生成提交信息

## 输出格式规则

1. **生成完成后直接输出提交信息**，不询问用户是否提交
2. 输出时用分隔线包裹，便于选中复制：

   ```
   --- 生成的 Commit 信息 ---
   feat(api): 添加用户注册接口

   - 新增 POST /api/register 端点
   - 添加邮箱格式验证
   Closes #42
   -------------------------
   ```

## 质量检查清单

- [ ] 仅读取已暂存变更（git diff --cached），不做其他检测
- [ ] 无已暂存变更时输出提示并终止
- [ ] type 从预定义列表中精确匹配
- [ ] subject 不超过 72 字符，中文祈使句，无句号
- [ ] body 仅在必要时使用
- [ ] footer 仅在 Breaking Change 或关联 Issue 时使用
- [ ] 不执行 git commit，不询问是否提交
- [ ] 输出信息用分隔线包裹，便于复制
