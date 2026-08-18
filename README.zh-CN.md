# Intent to Outcome Loop

面向编码 agent 的轻量、供应商中立**交付技能**（delivery skills）。七个小型技能，帮助 agent 以可验证、可评审的方式工作——而不变成一个平台。

这*不是* agent 运行时、调度器、工作流服务器、守护进程或项目管理系统。没有全局状态、任务看板、数据库或 Web UI。技能唯一可能产生的持久化产物都是按需创建的：一份 Reviewed Change 记录，以及——当用户明确要求时——`coordinate` 生成的一份 Handoff Markdown（快照，而非状态）。

## 它解决什么问题

当你认真使用编码 agent 时，困难的往往不是代码本身——而是决定要构建什么、针对风险选择合适粒度的流程、验证结果，以及在人与 agent 之间移交工作而不丢失上下文。这七个技能给 agent 一个统一而小巧的词汇表来应对这些部分。

## 七个技能

| 技能 | 作用 | 状态 |
| --- | --- | --- |
| `shape` | 可选。把一个不清楚的问题澄清为可交付就绪的 Brief：问题、目标、最小充分方案、交付不得自行发明的 material 业务语义、边界与成功标准。可能 challenge 过重的方案。在 Brief 之后停止，不会自动进入变更技能。 | 无 |
| `evaluate` | 用户主动调用的检查点。返回 CONTINUE / IMPROVE / PIVOT / STOP / INSUFFICIENT_EVIDENCE。从不自动运行。 | 无 |
| `task-router` | 默认入口。把任务分类为 Quick / Bounded / Reviewed 并移交给对应的变更技能。当 material 业务语义缺失时，返回 `shape` 而非重新访谈。只读。 | 无 |
| `quick-change` | 文档、文案、注释、格式等行为中立修改。 | 无 |
| `bounded-change` | 边界清晰的局部行为变更，带验证循环。 | 无 |
| `reviewed-change` | 架构、数据、安全、接口、跨模块变更。Change Contract → Falsification / RED → Plan Review → 分片 → Verification → 独立评审。 | 可选记录 |
| `coordinate` | 为人物/agent 与 agent/agent 交接生成 handoff、评审请求与结论摘要。 | 无 |

## 两种入口

- **大多数用户**只需要 `task-router`。给它一个软件任务，它会读取任务与代码，分类为 Quick / Bounded / Reviewed，填写一份简短 Route Brief（目标、边界、风险、验证），并且——如果你要求完成该任务且没有阻塞——**在同一对话中**移交给对应的变更技能。你不需要理解三个层级，也不需要重新输入技能名。
- **工程师**若已知层级，可直接调用 `quick-change`、`bounded-change` 或 `reviewed-change`。`task-router` 是便利入口，不是门槛。

`task-router` 本身从不编辑文件；"hand off（移交）"意味着由匹配的变更技能接管编辑。

## 需求–实现–评估飞轮

七个技能构成一个轻量的认知模型，而非强制流水线。没有唯一主入口技能，你也不必每轮运行全部技能。按你所在的环节取用：

```
需求不清楚？              shape
准备实现？                task-router → quick-change / bounded-change / reviewed-change
想评估结果？              evaluate   （仅当你调用它时）
需要切换人/agent/会话或请求评审？   coordinate
```

它如何保持用户驱动：

- **shape** 用于需求不清楚时——不是强制第一步。它以一份可交付就绪的 Brief 结束，不会自动移交给变更技能；只有当你要求继续时才移交。
- **task-router** 是当你想要完成任务时的默认入口；它在同一对话中移交给变更技能。已知层级的工程师可直接调用变更技能。
- **evaluate** 只能由你调用。任何技能或飞轮本身都不会自动触发它。
- **coordinate** 是按需连接器，用于切换人、agent、会话或请求评审——不是每轮都要经过的步骤。
- 飞轮是一种心智模型，而非生命周期状态机。

Core 始终面向个人、超级个体与小团队。它不是作为企业治理系统来宣传的。

## Core 与 Companion Skills

Core 提供跨项目骨干：目标与边界（`shape`）、风险成比例的路由（`task-router`）、承载证据的实现循环（`quick-change` / `bounded-change` / `reviewed-change`）、独立评审纪律（`reviewed-change`）、交接（`coordinate`）以及用户拥有的评估（`evaluate`）。

更深入的专业方法属于 **Companion Skills**——独立的、按需安装的技能，在特定任务中与 Core 组合使用，而非 Core 的安装依赖。例如（启发性质，非强制也非内置）：

- 难以复现的 bug 或性能回退 → 系统性调试
- 新行为或回归防护 → TDD
- 独立 diff 评审 → code review
- 浏览器行为 → 浏览器或端到端测试
- 安全 → security review
- 性能 → 性能剖析与测试
- 架构或简化 → architecture / code-simplification 技能
- 产品发现或 ROI → product-management / value-evaluation 技能

Core 不会复制这些方法的完整流程。当某个 Companion Skill 未安装时，Core 仍能独立工作——只是不应用那部分专业深度。不要把任何外部仓库或第三方技能当作 Core 的必需依赖。

### Companion Skills 推荐

Companion Skills 是推荐而非依赖——Core 从不要求某个特定的第三方技能。

两个常见起点：

**工程** —— IT / 正式软件开发

- 推荐：`tdd`、`diagnosing-bugs`、`code-review`
- 可选：`improve-codebase-architecture`、浏览器 / E2E 测试、安全评审、性能剖析

**原型** —— 任何构建可运行原型的人，包括业务、产品、设计与独立开发者

- 推荐：`frontend-design`
- 可选：`ui-ux-pro-max`、浏览器 / E2E 测试、`prototype`、`research`

各技能的覆盖范围与选择方式见 [docs/companion-skills.md](docs/companion-skills.md)。

## Quick vs Bounded vs Reviewed

选择**仍然安全的前提下最轻**的路径：

- **Quick** —— 行为中立、边界精确、极易回退。除了"没有改坏有意义的东西"，不需要验证行为。
- **Bounded** —— 影响行为，但限于单个函数/模块/小功能，有清晰边界与验证方法。记录 baseline，前后用同一方式验证，迭代实现而非目标。
- **Reviewed** —— 涉及架构、数据形态、安全、公共接口或跨模块。轻量流程：Change Contract → Falsification / RED → Plan Review → 纵向分片 → Verification → 最终独立评审 → 结论处理 → 需要时重新评审。

内置升级机制：影响行为的 Quick 变更升级为 Bounded；超出边界的 Bounded 变更升级为 Reviewed。

## 安装

要求：Python 3.8+（仅标准库）。

### Codex

```bash
python scripts/install.py --target codex --scope user
```

技能安装到 `~/.agents/skills`。`evaluate` 的仅用户可调用策略通过 `skills/evaluate/agents/openai.yaml` 强制执行。

### Claude Code

```bash
python scripts/install.py --target claude --scope user
```

技能安装到 `~/.claude/skills`。安装器会在已安装副本的 `evaluate` 中加入 `disable-model-invocation: true`，使 agent 无法自动调用它；只有显式用户调用才会运行。

### 选项

- `--scope project` —— 安装到**当前项目**（cwd）而非用户目录。目标路径取决于 host：
  - Codex：`<project>/.agents/skills`
  - Claude Code：`<project>/.claude/skills`
  - Antigravity：`<project>/.agents/skills`

  这里的项目指当前工作目录，绝不会是工具包自身位置或用户 home。
- `--dry-run` —— 只报告将要写入什么，不实际写入或删除任何内容。
- `--destination <dir>` —— 安装到显式目录，用于测试与非标准 host。覆盖基于 scope 的解析。使用单个 `--target` 时，技能直接写到 `<dir>` 下。
- `--target both --destination <dir>` —— 为 Codex 与 Claude **分别**安装到子目录 `<dir>/codex/` 与 `<dir>/claude/`，两个 host 视图互不覆盖。

安装器**绝不删除**目标目录中不相关的技能。它只写入自己拥有的技能。若目标技能已存在，安装器会报告哪些文件将被覆盖。

## 校验

```bash
python scripts/validate.py
```

检查技能清单、技能目录、frontmatter、行数预算、host 策略、本地路径泄漏与文档链接。出错时以非零码退出。

## 运行测试

```bash
python -m unittest discover -s tests -v
```

## OpenCode、Antigravity 与 Grok（实验性）

### OpenCode

```bash
python scripts/install.py --target opencode --scope user
```

技能安装到 `~/.config/opencode/skills`（project scope：`.opencode/skills`）。安装时会复制完整的技能包，包括每个技能的 `references/` 及其它支持文件。安装后的 `evaluate` 副本带 `metadata.opencode/autoinvoke: "false"`，OpenCode V2 会据此把它从模型的自动发现列表中隐藏，同时仍允许显式调用。OpenCode 稳定版 V1 能接受该 metadata frontmatter，但没有自动调用抑制能力，因此在 V1 上 `evaluate` 的仅用户可调用是约定而非强制。

OpenCode 目前仍为 **experimental**：原生适配器已通过机械验证，但真实运行时行为有待实际的 OpenCode pilot 验证。

### Antigravity

```bash
python scripts/install.py --target antigravity --scope user
```

技能安装到 `~/.gemini/config/skills`（project scope：`<cwd>/.agents/skills`）。安装时会复制完整的技能包，包括每个技能的 `references/` 及其它支持文件——不再需要手工复制。安装后的副本保持 canonical frontmatter 与正文，不添加任何 Antigravity 专属 metadata。Antigravity 通过把提示词与每个技能的 `description` 语义匹配来发现技能，且没有 per-skill 自动调用抑制能力，因此 `evaluate` 的仅用户可调用策略是操作者必须遵守的约定，而非 host 强制行为。

Antigravity 目前仍为 **experimental**：原生适配器已通过机械验证，但真实运行时行为有待实际的 Antigravity pilot 验证。

### Grok

Grok 可以直接以纯 markdown 读取 canonical 的 `SKILL.md` 文件——把 `skills/` 树手工复制到你的 host 技能目录。v0.4 尚未为 Grok 生成适配器元数据，因此在未来版本加入该元数据之前，`evaluate` 的仅用户可调用策略是操作者必须遵守的约定。完整兼容性表见 [docs/compatibility.md](docs/compatibility.md)。

## 许可证

MIT。见 [LICENSE](LICENSE)。

## 贡献

贡献规则见 [AGENTS.md](AGENTS.md)。本仓库不要求你使用自己的交付技能来维护它。
