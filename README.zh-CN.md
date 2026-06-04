# saygoal

> **说出目标，看着它达成**——给 Claude Code 与 Codex 的声明式 `/dec` + `/goal`，延续 Karpathy「给成功条件，然后看着它跑」的精神。

![/dec — 从命令式转声明式](./saygoal.TW.png)

[English](./README.md) | [繁体中文（台湾）](./README.zh-TW.md) | 简体中文 | [日本語](./README.ja.md)

> **主要 repo**：[`aeopress/saygoal.TW`](https://github.com/aeopress/saygoal.TW)（原于 [`yelban/andrej-karpathy-skills.TW`](https://github.com/yelban/andrej-karpathy-skills.TW) 维护，现已封存）

## 这是什么

`saygoal` 把模糊的命令式请求转成**可验证的契约**，再让 agent 自己 loop 到契约达成：

- **`/dec <任务>`** 把你的任务改写成成功条件 + 验证指令 + 边界，并产出一条可直接粘贴的 **`/goal` condition**。
- 把它贴进 Claude Code（或 Codex）内置的 **`/goal`**——一个小快模型每 turn 检查 transcript，盯着 agent 做到条件成立为止。

**30 秒范例：**

```
/dec 修登录页第一次加载时的闪烁

→ /goal "run npx playwright test login-flicker.spec.ts until it paste-shows 0 failures
         without changing the auth flow or any file outside the login component
         or stop after 20 turns"
```

`/dec` 写契约；`/goal` 跑到绿灯。支持 **Claude Code**（`/dec` command）与 **OpenAI Codex**（`$dec` skill — 七字段格式）。

→ [安装](#安装) · [运作原理](#dec--goal--工作流) · [为什么规则档不是重点](#为什么规则档不是重点--实证)

## `/dec` + `/goal` — 工作流

Karpathy 最强的洞见其实是**用户端的纪律**，不是 LLM 自我约束的事：

> 「LLM 非常擅长循环运行直到达成特定目标⋯⋯不要告诉它该做什么，给它成功标准然后看着它跑完。」

两个 slash command 刚好对应 Karpathy 那句「给成功条件 + 看着它跑」的**两个动词**：

| | `/dec`（本仓库） | `/goal`（Claude Code 内置，v2.1.139+） |
|---|---|---|
| 阶段 | **动手前**：把模糊请求改写成契约 | **动手中**：盯着 Claude 跑直到契约达成 |
| 动作 | 重写用户输入、**不动手** | 每 turn 后让小模型评估是否达标、没达标自动进下一 turn |
| 持久度 | 一次性转换、等你确认 | Session-scoped、直到 `/goal clear` |
| 评估者 | **你**（人工 review 契约） | **Haiku**（读 transcript 自动判 yes/no） |
| Karpathy 动词 | "give it success criteria" | "watch it go" |

### 何时声明式胜过命令式

| 命令式（杠杆弱） | 声明式（杠杆强） |
|---|---|
| 「加上输入验证」 | 「为这些无效输入写失败测试，然后让它们通过」 |
| 「修这个 bug」 | 「写一个能重现 bug 的测试，然后让它通过 — 其他测试必须还能过」 |
| 「让它更快」 | 「把这个负载下的 p95 延迟压到 X ms 以下；用 `scripts/bench.sh` 量」 |
| 「重构 X」 | 「重构 X 但不能改变可观察行为；既有测试必须还能过」 |

- **声明式**：有可观察结果的功能、bug 修复、性能工作、有测试覆盖的重构。
- **命令式**（跳过 `/dec`）：探索性编辑、UI 微调、文字创作、任何「完成」标准主观的工作。

连同目标一起给 agent 验证手段：测试指令、benchmark 脚本、lint 指令、给视觉检查的 browser MCP。然后放手让它迭代。

### 单独用 `/dec`

`dec` 是 **declarative**（声明式）的缩写。指令把命令式需求改写成契约；你确认后才会动工。

```
/dec 修登录页第一次加载时的闪烁
```

回复会给你成功条件（例如「Playwright 截屏比对 10 次、位移 < 2px」）、一条措辞成「Claude 必须实际运行并贴出输出」的验证指令、以及按需出现的边界（不可改动 / 可写路径 / 外部系统限制）——**外加一条可直接拷贝粘贴的 `/goal` condition**（自然语言的 `[做什么] until [端状态] without [约束] or stop after 20 turns` 句式）。若任务太主观或太小，会回「不适用，建议直接做」、不硬转换。适合单一 prompt 套用声明式纪律、不需要自主迭代的场合（或在 Cursor / 旧版 Claude Code 没有 `/goal` 时）。

### `/dec` 当作 `/goal` 的「边界设置器」

`/goal` 的效果完全取决于你给它的 condition 字符串。写不好的 condition 永远不会收敛：

```
❌ /goal "登录页不要闪烁"
   Haiku 怎么判定「不闪烁」？看截屏？读 console？
   结果 evaluator 一律回 yes 或一律回 no、loop 永远不收敛。

✅ /dec 修登录页第一次加载时的闪烁
   →  成功条件：Playwright 截屏比对 10 次、位移 < 2px
       验证指令：运行 `npx playwright test login-flicker.spec.ts` 并贴出显示 0 failures 的输出
       边界：写入限定在登录组件；不动 auth 流程

✅ /goal "run npx playwright test login-flicker.spec.ts until it paste-shows 0 failures
          without changing the auth flow or any file outside the login component
          or stop after 20 turns"
   Haiku 读 transcript 内贴出的测试输出能精准判定。
   Loop 真的会收敛。
```

`/dec` 强制设置 `/goal` 自己给不出的三件事：

1. **可机器判定的成功条件**——「diff < 2px」「10 passed」「p95 < X ms」evaluator 看 transcript 就能 yes/no
2. **嵌进契约的验证指令**——强迫 Claude 真的去跑检查、而不是静态推理然后回报「应该可以了」（这正是我们 T4 declarative-loop 测试看到的失败模式）
3. **结构化边界（五面、按需）**——不可改动、可写路径、外部系统限制、何时暂停、回合上限。对 Claude 这些会编进 condition（「… without test files changed and no new files in src/legacy/, or stop after 20 turns」）；其中「何时暂停」单独列出、建议用 Stop hook，因为 evaluator 判不了它。

### 完整 pipeline

```
1. /dec <模糊需求>                 ← 契约 + 一条编好的 /goal condition
2. 你 review 契约                  ← 人类确认方向
3. 拷贝 #1 那条 /goal 指令粘贴     ← Haiku 接手当判官
4. Claude 自主 loop 到收敛          ← Karpathy 说的「watch it go」
```

### Codex `/goal` 也适用

OpenAI 的 Codex CLI 比 Claude Code 早 11 天，在 [v0.128.0（2026-04-30）](https://developers.openai.com/codex/cli/slash-commands) 推出自家的 `/goal`。Codex [官方 goal 写法指南](https://developers.openai.com/codex/use-cases/follow-goals)列出好的 goal 应该明确的四件事：

> "what Codex should achieve, what it shouldn't change, how it should validate progress, and when it should stop"

并明确指出 **"Codex should know what 'done' means before it starts."** 这正是 `/dec` 写出来的契约：

| Codex docs 要求 | `/dec` 对应输出（Codex 七字段） |
|---|---|
| what Codex should achieve | **Outcome** |
| what it shouldn't change | **Constraints + Boundaries** |
| how it should validate progress | **Verification** |
| when it should stop | **Stop when + Pause if** |

开 Codex `/goal` 之前先跑 `dec` 的三个 confirmed value：

1. **你不用记 Codex 那条 checklist**——`/dec` 的 template 每次都把七个 Codex 字段（outcome、verification、constraints、boundaries、iteration policy、stop、pause）填满。
2. **`/dec` 要求每个字段都可量测**——[`plugin/commands/dec.md`](./plugin/commands/dec.md) 要求「可验证的端状态，且必须是 `/goal` 的 evaluator 在 transcript 里找得到的证据：指令退出码、输出比对、可量化门槛」。Codex docs 虽然主张 goal 应该可测试，但没附样板在 user 端强制运行这件事。
3. **`/dec` 对主观任务的「不适用，建议直接做」short-circuit**（UI 微调、文案、单行 rename）—— Codex `/goal` 没有 documented 等价功能。对主观任务开 `/goal` 正是 Codex docs 警告的：**"Avoid using a goal for a loose list of unrelated work."**

**`dec` 与 Codex 搭配使用**：本仓库也提供 Codex 版的 `dec` skill（透过 Codex plugin 打包，位于 [`plugins/saygoal`](./plugins/saygoal)），输出 Codex 的七字段 `/goal` 模板（Claude command 则输出单一条自然语言 condition——两边各自产出宿主的原生格式）。在 Codex CLI 可用 `$dec <request>` 叫用，或透过 `/skills` 选取；它输出的 `/goal` 区块可以直接贴到 Codex `/goal "..."`。这不会改变 Claude Code 的 `/dec`：原本的 command 仍在 [`plugin/commands/dec.md`](./plugin/commands/dec.md)，也仍然使用 Claude 的 `$ARGUMENTS` template。

> **Caveat——这是设计层面的声明、不是实证。** 我们**没有**对 `/dec` + Codex `/goal` 跑控制组实验。上面的对应是读 `/dec` 的 prompt template 对照 Codex [published goal-writing guidance](https://developers.openai.com/codex/use-cases/follow-goals) 推得。[`EXPERIMENT.md`](./EXPERIMENT.md) 那个 N=40 A/B 测的是 CLAUDE.md 对 Opus 4.7 的效应、不是 `/dec` 本身。

> **调用名称注意**：透过插件（选项 A）安装时，Claude Code 会把指令 namespace 成 `/saygoal:dec`。想要短的 `/dec`，请用选项 C 手动安装。内置的 `/goal` 不受安装方式影响、永远可用。

> **`/goal` 评估者注意**：`/goal` 把每 turn 的 transcript 喂给 Claude Code 内置的「small fast model」slot、[默认是 Haiku](https://code.claude.com/docs/en/goal.md)。**没有 `/goal` 专属的 model 设置**；唯一替换方式是用 `ANTHROPIC_DEFAULT_HAIKU_MODEL` 环境变量整体 redirect 那个 slot（[model config 文档](https://code.claude.com/docs/en/model-config.md)）——但这会把 `haiku` alias 全部换掉、不只 `/goal`。一般使用不需动。

## 安装

### Claude Code

```
/plugin marketplace add aeopress/saygoal.TW
/plugin install saygoal@saygoal
```

装好后用 `/saygoal:dec <任务>`。内置 `/goal` 永远可用、不需安装。

### Codex

clone 本 repo 后、在 root 运行：

```
codex plugin marketplace add .
codex plugin add saygoal@saygoal
```

用 `$dec <任务>`（或从 `/skills` 选），再把产出的 `/goal "..."` 贴进 Codex 内置 `/goal`。

<details>
<summary><b>高端</b> — 短 <code>/dec</code>、可选的 <code>CLAUDE.md</code> 规则、自动更新、Cursor</summary>

**短 `/dec`（免 namespace）。** 插件会把指令 namespace 成 `/saygoal:dec`。想要短的 `/dec`，把指令档放到全域：

```bash
mkdir -p ~/.claude/commands
curl -o ~/.claude/commands/dec.md \
  https://raw.githubusercontent.com/aeopress/saygoal.TW/main/plugin/commands/dec.md
```

**三条 `CLAUDE.md` 规则（可选）。** 我们的 [A/B 实证](./EXPERIMENT.md) 显示对 Opus 4.7/4.8 没有可测量效应——想要才装：

```bash
curl -o CLAUDE.md https://raw.githubusercontent.com/aeopress/saygoal.TW/main/CLAUDE.md
# 或只把规则追加到既有 CLAUDE.md：
# curl -s https://raw.githubusercontent.com/aeopress/saygoal.TW/main/CLAUDE.md | sed -n '/^## Stop when confused/,$p' >> CLAUDE.md
```

**自动更新的短 `/dec`。** clone 一次再 symlink，`git pull` 就会保持最新：

```bash
mkdir -p ~/.claude/external ~/.claude/commands
git clone https://github.com/aeopress/saygoal.TW ~/.claude/external/saygoal.TW
ln -sf ~/.claude/external/saygoal.TW/plugin/commands/dec.md ~/.claude/commands/dec.md
# 之后更新：cd ~/.claude/external/saygoal.TW && git pull
```

**Cursor。** 本仓库附 [`.cursor/rules/karpathy-guidelines.mdc`](.cursor/rules/karpathy-guidelines.mdc)（`alwaysApply: true`）；详情见 [`CURSOR.md`](./CURSOR.md)。

</details>

## 为什么规则档不是重点 — 实证

`saygoal` 也附一份三行的 `CLAUDE.md`（内容衍生自 [Andrej Karpathy 对 LLM 编码陷阱的观察](https://x.com/karpathy/status/2015883857489522876)）。它是可选的，而 A/B 实证说**规则档几乎不动模型**——杠杆在 `/dec` + `/goal`。本节是证据，当背景看即可。

### 现况（Opus 4.8 时代 · 2026 年 5 月）

Anthropic 自己的 Claude Code 提示词、演进方向跟这个 skill 一模一样。v1→v2 拿掉了模型已内化的 explicit guardrail（66 行 → 19 行）。Opus 4.7 已经把大部分 guardrail 塞进一份冗长的系统提示词；**Opus 4.8（2026-05-28）更进一步、改用 *lean* prompt 把它们整段拿掉**——这些规则现在活在 post-training（model weights）、不在 prompt 文字里。

我们在 4.8 上重跑了 A/B（T1、N=10）：抓 bug 率从 **33% 跃升到 90%**、而三组 `CLAUDE.md`（v1／v2／无）统计上仍持平。模型把纪律吸收进去了；剩下的杠杆在用户端——`/dec` + `/goal`。**新版刻意只保留系统提示词还未涵盖的部分。** 旧版完整四原则保留在 [`archived/v1/`](./archived/v1/) 供参考。

### 给 LLM 看的三条 reminder

三条 reminder，与 [`CLAUDE.md`](./CLAUDE.md) 完全一致。保留是因为成本低、在不同模型或更长的上下文中可能仍有用；但在 Opus 4.7 上实证边际效应不显著（见 [`EXPERIMENT.md`](./EXPERIMENT.md)）。

1. **困惑时停下** — 请求语意不清时，明确指出哪里不清楚并提问；不要默默挑一个解读就动手。
2. **每一行改动都要对应到请求** — 回报完成前，重看自己的 diff；任何没有直接服务用户目标的行就删掉。
3. **以声明式目标跑 loop** — 当存在可验证的终态时，自主驱动直到达成。

整个指令档就这样。Karpathy 列出的其他陷阱（过度复杂化、顺手重构、推测性功能、死码累积、删掉模型「看不顺眼」的注解⋯⋯）都已经被 Claude Code 默认系统提示词涵盖；在这里重述只会稀释信号。

### 哪些 v1 规则被归到哪里

[上游 v1](./archived/v1/CLAUDE.md) 有 4 大原则 × 每个 4–6 条 sub-rule（共 66 行）。v2 只剩 19 行。下表是**逐字验证**过的对照——第三栏每一格都是我们在实际 Claude Code session 直接观察到的系统提示词原文，不是改写过的近似句。[^sysprompt]

> **更新——Opus 4.8（2026-05-29）：** 4.8 把 **lean system prompt** 设为 default、下表第三栏那**八条 quote 在 4.8 全部消失了**——4.7 的 `# Doing tasks` / `# Executing actions with care` 大段被压缩成 5 条 bullet 的 `# Harness`。这**不推翻**论点——我们在 4.8 上重跑了实验确认。T1（N=10、固定 automated scorer）上「两 bug 都修」从 **33% 跃升到 90%**（Fisher p=1.1e-5、少漏约 6.7 倍、吻合 Anthropic「漏放瑕疵几率低约 4 倍」），而三组（v1 65 行／v2 19 行／无 `CLAUDE.md`）**统计上仍持平**（两两 p ≥ 0.47）。也就是 guardrail 从 *prompt* 移到了 *post-training（model weights）*、不是消失——CLAUDE.md flavor 依然测不出效应。重述模型已内化的规则仍是浪费信号、而 prompt 越干净、19 行的文件越容易保持精准。完整 4.7→4.8 diff 见 [`2026-05-29-opus-4.8-cli.md`](./archived/observed-system-prompts/2026-05-29-opus-4.8-cli.md)；重跑数据与 caveat 见 [`EXPERIMENT.md`](./EXPERIMENT.md)（§ Opus 4.8 re-run）。下表因此是**对 4.7 历史准确**（已独立验证）、并加注说明、不是默示它符合当前 default prompt。

| v1 条文 | v2 处置 | 系统提示词逐字 quote |
|---|---|---|
| **Simplicity First** — 不加超出请求范围的功能 | 删 | "Don't add features, refactor, or introduce abstractions beyond what the task requires" |
| **Simplicity First** — 单次使用的代码不抽象 | 删 | "Three similar lines is better than a premature abstraction" |
| **Simplicity First** — 不加没人要的 flexibility / configurability | 删 | "Don't design for hypothetical future requirements" |
| **Simplicity First** — 不为不可能发生的场景写错误处理 | 删 | "Don't add error handling, fallbacks, or validation for scenarios that can't happen. Trust internal code and framework guarantees. Only validate at system boundaries" |
| **Surgical Changes** — 不顺手改邻近代码 | 删 | "A bug fix doesn't need surrounding cleanup; a one-shot operation doesn't need a helper" |
| **Surgical Changes** — 没人要你改前不要删掉既有死码 | 删 | "Avoid backwards-compatibility hacks like renaming unused _vars... If you are certain that something is unused, you can delete it completely" |
| **Surgical Changes** — 每一行改动都要对应到请求 | **保留**（重命名） | *（无对应——这条是 v2 真正补强的）* |
| **Think Before Coding** — 整个原则（4 条 sub-rule） | **3 删 1 留**（留下的改名 Stop when confused） | *（无逐字对应——见下方说明）* |
| **Goal-Driven Execution** — TDD 范例 + 多步计划格式 | **改写**为 Loop on declarative goals | *（无对应——这是 Karpathy 真正的洞见、留下但重新诠释）* |

关于 **Think Before Coding** —— 我们删了它的三条 sub-rule（「明确说出假设」「列出多种解读」「合理时要 push back」），但这三条**并非**逐字被系统提示词涵盖。最接近的段落是 `"For exploratory questions, respond in 2–3 sentences with a recommendation and the main tradeoff. Present it as something the user can redirect"`——意图相近、但**不是完整替代**。我们还是删了，因为 [A/B 实证](./EXPERIMENT.md) 显示放入完整四条版本也没能可靠触发「停下来问」（T1 共 30 runs 中 0 次在动手前问澄清）。唯一保留的「不确定时停下来问」是因为它的动作最干净（直接停），不是因为其他三条被覆盖。**这格是设计判断、不是「逐字重复所以删」的主张。**

#### 删除的三个具体好处

1. **信号去稀释**。在 `CLAUDE.md` 重述系统提示词已有的内容，会给模型已经会做的事再加一份权重；新加进来的规则就要跟这些重复条目抢注意力。v2 的每一行都在说系统提示词**没说**的事。
2. **降低非编码任务的误触**。v1 的 TDD-first 范例（「为无效输入写测试、再让它通过」）写死了可测试情境。UI 微调、文案、设置档编辑都没有测试可写——v1 框架会逼模型，在不该发明验证条件的地方发明验证条件。v2 的 `## Loop on declarative goals` 改成把验证条件的决定权还给用户、不规定格式。
3. **「更短不会更糟」的实证背书**。[N=40 A/B 测试](./EXPERIMENT.md) 显示在 Opus 4.7 上、v1（65 行）／v2（19 行）／无 `CLAUDE.md` 三组无统计显著差异。删到只剩 19 行不会可测量地变差——而且文件越短、与项目规则冲突时的 review 成本越低。

#### policy / mechanism 分离

Karpathy 列的陷阱中、v2 *没有*删掉的那条最重要：**`Loop on declarative goals`**。它能活下来、第一个原因是系统提示词没涵盖——但更关键的原因是、这件事的杠杆在**用户端**、不在 LLM 自我约束。这也是为什么 saygoal 提供 `/dec`：一个把命令式请求改写成声明式契约的 slash command、搭配内置的 `/goal` evaluator（详见上方 [工作流](#dec--goal--工作流)）。

这个「policy / mechanism 分离」——LLM 处理「想要什么」（high-level intent）、工具处理「怎么达成」（deterministic execution）——在 2025–2026 的研究文献中已经收敛成主流范式（[arxiv 2510.04607](https://arxiv.org/html/2510.04607v2)、[PDL arxiv 2410.19135](https://arxiv.org/pdf/2410.19135)）。`/dec` 是这个范式在 prompt 工程层的对应接口。

### A/B 实证告诉我们什么

上方那张 v1→v2 逐字对照表是「为什么新版这么短」的论证——v1 大部分内容已在系统提示词里。但这是观察判断、不是量测。所以 2026 年 5 月我们跑了小型 A/B 实证：

- 3 组：无 CLAUDE.md / v1 上游版（65 行）/ v2 我们版（19 行）
- 4 个诱发 Karpathy 痛点的 toy task + 最区分维度 T1 ambiguous-bug 加码到每组 N=10
- 受测模型：Opus 4.7；盲判官（blind judge）：Sonnet 4.6

**结果：三组没有统计显著差异。** T1 加码到每组 N=10 后三组全部 7/10 正确、Fisher exact p = 1.000。30 次 runs 中 **0 次**在编辑前问澄清（clarification）——不论哪版规则都没能可靠触发「停下来问」。

诚实版结论：在这个 toy task 规模上、CLAUDE.md（不论哪版）对 Opus 4.7 行为的边际效应**小到 N=10 测不出来**。**任选一版皆可；用户端的声明式描述方式（user-side declarative framing，就是 `/dec` 在做的事）杠杆可能比规则档本身大。**

完整数据、scripts、caveats、以及 Phase 1 (N=3) 一度看起来「v1 显著优于 v2」最后被 Phase 2 (N=10) 摊平的过程：[`EXPERIMENT.md`](./EXPERIMENT.md)（英文）。

## 与上游的关系

本仓库是 [`forrestchang/andrej-karpathy-skills`](https://github.com/forrestchang/andrej-karpathy-skills) 的繁体中文（台湾）在地化 fork，为 Claude Code Opus 4.7 → 4.8 时代更新内容。Plugin / marketplace 命名为 `saygoal`；README 为双语（英文 + 繁体中文）。

## 授权

[MIT](./LICENSE) — Copyright © 2026 yelban。

详细出处说明见[与上游的关系](#与上游的关系)章节。

[^sysprompt]: 第三栏的逐字 quote 是 2026-05-28 在 Claude Code CLI session 直接观察到的 Opus 4.7 系统提示词。完整观测 snapshot 存于 [`archived/observed-system-prompts/2026-05-28-opus-4.7-cli.md`](./archived/observed-system-prompts/2026-05-28-opus-4.7-cli.md)（英文）——该文件说明系统提示词与 `CLAUDE.md` 注入，在 session 结构中如何位置上可分离，并把表格每一条 quote 都对应到 snapshot 内精确位置。**Opus 4.8（2026-05-29）改用 lean prompt、把这八条 quote 全部拿掉**——4.7→4.8 diff 见 [`2026-05-29-opus-4.8-cli.md`](./archived/observed-system-prompts/2026-05-29-opus-4.8-cli.md)。Claude Code 系统提示词是 runtime 注入、Anthropic 并未公开文档化；措辞随 CLI／模型更新改变（4.7→4.8 是一次大改）。
