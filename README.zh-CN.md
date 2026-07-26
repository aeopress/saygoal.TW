# saygoal

> **说出目标，看着它达成**——给 Claude Code 与 Codex 的声明式 `/dec` + `/goal`，延续 Karpathy「给成功条件，然后看着它跑」的精神。

![/dec — 从命令式转声明式](./saygoal.TW.png)

[English](./README.md) | [繁体中文（台湾）](./README.zh-TW.md) | 简体中文 | [日本語](./README.ja.md)

> **主要 repo**：[`aeopress/saygoal.TW`](https://github.com/aeopress/saygoal.TW)（原于 [`yelban/andrej-karpathy-skills.TW`](https://github.com/yelban/andrej-karpathy-skills.TW) 维护，现已封存）

## 这是什么

`saygoal` 把模糊的命令式请求转成**可验证的契约**，再让 agent 自己 loop 到契约达成：

- **`/dec <任务>`** 把你的任务改写成成功条件 + 验证指令 + 边界，并产出一条可直接粘贴的 **`/goal` condition**。
- 把它贴进 Claude Code（或 Codex）内置的 **`/goal`**——一个小快模型每 turn 检查 transcript，盯着 agent 做到条件成立为止。
- **`/saygoal:retro`**——`/goal` loop 停滞时，把 transcript 当搜索 trace 读、诊断卡点，结构性重写契约（修订版 condition＋一行 rollback）。

**30 秒范例：**

```
/dec 修登录页第一次加载时的闪烁

→ /goal "run npx playwright test login-flicker.spec.ts until it paste-shows 0 failures
         without changing the auth flow or any file outside the login component
         or stop after 12 turns"
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

回复会给你成功条件（例如「Playwright 截屏比对 10 次、位移 < 2px」）、一条措辞成「Claude 必须实际运行并贴出输出」的验证指令、以及按需出现的边界（不可改动 / 可写路径 / 外部系统限制）——**外加一条可直接拷贝粘贴的 `/goal` condition**（自然语言的 `[做什么] until [端状态] without [约束] or stop after 12 turns` 句式）。若任务太主观或太小，会回「不适用，建议直接做」、不硬转换。适合单一 prompt 套用声明式纪律、不需要自主迭代的场合（或在 Cursor / 旧版 Claude Code 没有 `/goal` 时）。

**先问清楚，再编译（grilling 前置）**：好契约要能收敛，前提是没有未解问题。所以面对模糊请求，`/dec` 会在编译前先 grill——一次只问一题、每题附上建议答案，把只能靠猜的字段（门槛、验证目标存不存在、可写边界）问掉，而不是默默标 `(assumed)` 带过。三种行为一目了然：**模糊任务** → 一次一题、问到收敛；**太主观或太小** → 回「不适用，建议直接做」；**清楚且够分量** → 不啰嗦、直接编出契约。skip-when-clear 护栏让它只在真正需要时才追问，不骚扰已经精确的请求（行为已用 Codex CLI 实测通过）。Claude Code 团队成员 Thariq 描述的 Fable 5 工作法正是这个流程——"I'd ask Claude to interview me about the implementation before writing the final spec file"（[来源视频](https://x.com/trq212/status/2073100352921215386)）。

**给上下文，不只给约束（context, not constraints）**：Thariq 视频里最精华的一招——与其说「保持简单、别过度设计」，不如说「这是实验功能，一个月后很可能删掉，别建丢弃起来会心疼的东西」。约束只能列举「不要做什么」；上下文让 agent 在约束没预料到的情况下自己做对决定。所以 `/dec` 遇到品味式约束不会照抄进契约，而是 grill 出底层原因（实验？寿命？期限？——这题选项固定，Claude 版用 AskUserQuestion 单选），编成契约的可选「任务上下文（Context）」字段——Claude 版以一短句带进 `/goal` condition 开头（evaluator 只判 until / without 部分，上下文是给实现 agent 读的），Codex 版是七字段外的可选 `Context:` 行。

**多子项规范 → 逐项差异报告**：规范列了多个子项时，契约会把验证延伸为「贴出逐项实现报告：每项标 implemented / deviated 并说明差异」——对应 Thariq 的 "prepare a report on what was implemented and if anything differed"。报告是 evaluator 可 pattern-match 的证据，也堵住最隐蔽的失败模式：loop 收敛了，但建的不是你要的东西。报告默认由实现者自报；Claude 版在多子项时 grilling 会多问一题，可升级为 **workflow 独立验证**——每个子项派一个独立验证 agent、只对照规范与成果、不看实现过程——正是 Thariq 的 "use a workflow to verify each part of the plan"。独立验证可信（自报是自己改考卷）但较花 token，所以做成选项、默认自报。

**搜索型任务 → 收敛护栏**：任务要靠多轮「尝试→验证→再尝试」才收敛（性能调优、flaky test 排查、追 benchmark 数字）时，loop 的典型死法是同状态下重提同一改法、连续失败到回合上限——LLM 退回自身 priors。这正是 [Bilevel Autoresearch](https://arxiv.org/abs/2603.23420) 在 Karpathy 自己的 pretraining benchmark 上记录到的失败模式，而它的解法——打破内圈的固定搜索模式——搬到 `/dec` 上就是以契约为机制载体：编译出的 condition 会多两条护栏——until 段的 **trace 条款**（`pasting every 5 turns a one-line search log: approaches tried → result → ruled out`），让 transcript 保持可诊断的搜索记录；without 段的 **anti-fixation 条款**（`without repeating an approach whose verification output has already failed twice`），相当于论文 Tabu Search 机制的 prompt 版。非搜索型任务两条都不加：在那里它们是噪音。

### 契约的两种吃法 —— spec 模式 vs loop 模式

同一份契约有两种消费方式；按任务挑，不要按习惯挑：

- **Spec 模式**——把契约（#1–#4 字段，不含 `/goal` 前缀）交给单次实现——自己这个 session 或委派出去的模型——收工时照 Verification 字段验收。Claude 5 世代模型对规格完整的问题常能一次做对，契约正是那份规格；单发实现也省掉 loop 的每回合成本（重读 context、重跑验证）。确定性任务先试这条。
- **Loop 模式**——任务真的需要受监督的迭代时，才把编译好的 `/goal` condition 贴上：搜索型任务（性能调优、flaky test、追 benchmark 数字）、想要 harness 把关的委派、或无人值守。在新一代模型上，loop 的价值是收敛保证与证据诚实性——一个说不动的 evaluator——而不是「让模型持续工作」。

两条路的验收标准完全相同：契约不变，变的只是谁来开车。

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
          or stop after 12 turns"
   Haiku 读 transcript 内贴出的测试输出能精准判定。
   Loop 真的会收敛。
```

`/dec` 强制设置 `/goal` 自己给不出的三件事：

1. **可机器判定的成功条件**——「diff < 2px」「10 passed」「p95 < X ms」evaluator 看 transcript 就能 yes/no
2. **嵌进契约的验证指令**——强迫 Claude 真的去跑检查、而不是静态推理然后回报「应该可以了」（这正是我们 T4 declarative-loop 测试看到的失败模式）
3. **结构化边界（五面、按需）**——不可改动、可写路径、外部系统限制、何时暂停、回合上限。对 Claude 这些会编进 condition（「… without test files changed and no new files in src/legacy/, or stop after 12 turns」）；其中「何时暂停」单独列出、建议用 Stop hook，因为 evaluator 判不了它。回合上限把验证成本算进去：loop 每回合都重跑验证，验证昂贵（整包 e2e、长 benchmark）就下调上限——或契约改编便宜的针对性验证逐回合跑、全套留到收尾跑一次。

### 完整 pipeline

```
1. /dec <模糊需求>                 ← 契约 + 一条编好的 /goal condition
2. 你 review 契约                  ← 人类确认方向
3. 拷贝 #1 那条 /goal 指令粘贴     ← Haiku 接手当判官
4. Claude 自主 loop 到收敛          ← Karpathy 说的「watch it go」
5. loop 停滞？/saygoal:retro       ← 读 trace、重写契约（外圈）
```

### loop 停滞时 —— `/saygoal:retro`，外圈

`/goal` loop 可能停滞：撞到 `or stop after 12 turns` 时还在重提同一失败修法的变体。把原 condition 直接重挂是唯一保证没用的一招——[Bilevel Autoresearch](https://arxiv.org/abs/2603.23420) 的消融实验里，参数级调整没有可靠增益，整个 5× 效果都来自机制级重写。`/saygoal:retro` 就是这条 pipeline 的外圈：把停滞 session 的 transcript 当搜索 trace 读，判定停滞类别——验证断裂、门槛不可达、边界墙住正解（自动并入的约束列头号嫌疑）、固着、范围错置——然后结构性重写契约。输出是一条可直接粘贴的修订版 condition，外加一行 `rollback:` 照抄原版——坏的重写最多只花你一次粘贴。每次 retro 还会在 `.claude/saygoal.history.jsonl` 补一行记录，之后的 `/dec` grilling 会先读它——过去的停滞原因变成下一份契约的前置查证。

### 契约也是委派 prompt —— 与 Codex 委派工具协作

`/dec` 的输出不只能喂 `/goal`。一份好的委派 prompt 需要五件事——上下文、明确目标、约束、输出格式、完成判据——而这正好是契约的字段。所以同一份契约也可以整段（不含 `/goal` 前缀）直接当作委派 prompt：

- **[openai/codex-plugin-cc](https://github.com/openai/codex-plugin-cc)**（`/codex:rescue`）：`/dec` 先把模糊需求编成契约，再 `/codex:rescue --background <契约全文>` 丢给 Codex 后台执行。收割（`/codex:result`）时照契约的验证字段验收；逐项差异报告让你只读最终输出就能判断有没有偏离，不用回看过程。
- **[codex-orchestrator](https://github.com/yelban/codex-orchestrator)**（`codex-agent` CLI）：并行 fan-out 多个任务时，每个 `codex-agent start "<契约>"` 都带着自己的验证与边界；`await-turn` 收割后照 Verification 验收即可。
- **`codex exec`**（裸 codex CLI——最通用的通道，不需装任何 plugin）：把 `codex exec -C <repo> --sandbox workspace-write --json "<契约>"` 当后台 task 派发。后台 task ID、`--json` 事件流、完成通知、TaskStop 就是运行状态追踪——等同 codex-orchestrator 包装的 PID + exitcode + JSONL log，由 Claude 后台 task 原生提供。这是 `/codex:rescue`、`codex-agent` 都不可用时的最低共同标准 fallback（需网络——Claude 在 sandbox 下要放行）。

Claude 版的 `/dec` 会把这件事自动化：契约输出后检测这几个通道（看 session 的 skills 清单、`command -v codex-agent`、`command -v codex`），检测到就用 AskUserQuestion 问执行通道——自己 `/goal` loop，还是委派出去。你的选择记在项目的 `.claude/saygoal.local.json`，下次排在第一个选项；但**每次仍会问**（每次委派都花额度，单次否决权留在你手上）。选了委派就当场后台派发，收割时照契约的验证字段验收。都没安装就不会提委派，行为与从前相同。

分工是上下游：`/dec` 管「契约写得够不够收敛」，委派工具管「谁去执行、怎么并行」。同一份契约，贴 `/goal` 是自己 loop 到绿灯，交给委派工具是外包给另一个模型——验收标准不变。

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

**`dec` 与 Codex 搭配使用**：本仓库也提供 Codex 版的 `dec` skill（通过 Codex plugin 打包，位于 [`plugins/saygoal`](./plugins/saygoal)），输出 Codex 的七字段 `/goal` 模板（Claude command 则输出单一条自然语言 condition——两边各自产出宿主的原生格式）。在 Codex CLI 可用 `$dec <request>` 调用，或通过 `/skills` 选取；它输出的 `/goal` 区块可以直接贴到 Codex `/goal "..."`。这不会改变 Claude Code 的 `/dec`：原本的 command 仍在 [`plugin/commands/dec.md`](./plugin/commands/dec.md)，也仍然使用 Claude 的 `$ARGUMENTS` template。

> **Caveat——这是设计层面的声明、不是实证。** 我们**没有**对 `/dec` + Codex `/goal` 跑控制组实验。上面的对应是读 `/dec` 的 prompt template 对照 Codex [published goal-writing guidance](https://developers.openai.com/codex/use-cases/follow-goals) 推得。[`EXPERIMENT.md`](./EXPERIMENT.md) 那个 N=40 A/B 测的是 CLAUDE.md 对 Opus 4.7 的效应、不是 `/dec` 本身。

> **调用名称注意**：通过插件（选项 A）安装时，Claude Code 会把指令 namespace 成 `/saygoal:dec`。想要短的 `/dec`，请用选项 C 手动安装。内置的 `/goal` 不受安装方式影响、永远可用。

> **`/goal` 评估者注意**：`/goal` 把每 turn 的 transcript 喂给 Claude Code 内置的「small fast model」slot、[默认是 Haiku](https://code.claude.com/docs/en/goal.md)。**没有 `/goal` 专属的 model 设置**；唯一替换方式是用 `ANTHROPIC_DEFAULT_HAIKU_MODEL` 环境变量整体 redirect 那个 slot（[model config 文档](https://code.claude.com/docs/en/model-config.md)）——但这会把 `haiku` alias 全部换掉、不只 `/goal`。一般使用不需动。

## 安装

### Claude Code

```
/plugin marketplace add aeopress/saygoal.TW
/plugin install saygoal@saygoal
```

装好后用 `/saygoal:dec <任务>`。内置 `/goal` 永远可用、不需安装。

> **从旧版升级？** 本项目前身是 `andrej-karpathy-skills.TW`（marketplace 名 `karpathy-skills`，旧 repo 已封存）。若你在改名前装过，先移除旧 marketplace，否则收不到更新。`marketplace remove` 会一并卸载旧 plugin：
>
> ```
> /plugin marketplace remove karpathy-skills
> /plugin marketplace add aeopress/saygoal.TW
> /plugin install saygoal@saygoal
> /reload-plugins
> ```

### Codex

直接从 GitHub 安装（与 Claude Code 的 marketplace 指令对称）：

```
codex plugin marketplace add aeopress/saygoal.TW
codex plugin add saygoal@saygoal
```

或先 clone 本 repo，把第一行换成 `codex plugin marketplace add .`（在 repo root 运行）。

用 `$dec <任务>`（或从 `/skills` 选），再把产出的 `/goal "..."` 贴进 Codex 内置 `/goal`。

若要使用可选的固定模型派工，先明确确认这份契约，再调用 `$execute-goal`。第一次使用时，它会检测内附的 `saygoal_writer` custom-agent 模板是否已安装，并提供项目级（`.codex/agents/`）或个人级（`~/.codex/agents/`）设置；设置后开新 thread，再调用一次。它会启动主 thread 的 `/goal`、只派一个 `gpt-5.6-sol`／`high` writer，最后由主 thread 独立重跑验证。

`$execute-goal` 不会默默换成未钉选模型；若环境没有该模型或不能选择 custom agent，会在改文件前暂停。这是 Codex-only 功能，Claude Code 的 `/saygoal:dec` 完全不变。

- **更新**：`codex plugin marketplace upgrade saygoal`，再重跑 `codex plugin add saygoal@saygoal`。
- **移除**：`codex plugin remove saygoal@saygoal`，再 `codex plugin marketplace remove saygoal`。

<details>
<summary><b>进阶</b> — 短 <code>/dec</code>、可选的 <code>CLAUDE.md</code> 规则、自动更新、Cursor</summary>

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

## 加码指令：`/saygoal:repo-audit`

Plugin 也附带 `/saygoal:repo-audit`——principal 级别的只读 repo audit（改编自 [OmerFarukOruc 的 `/repo-audit` gist](https://gist.github.com/OmerFarukOruc/753f95b1ac278b683be83ed26b3bcc1f)，为 saygoal 工作流调校）。它会先画出 repo map，再按 audit 维度并行展开 subagents、挖 git 历史找 churn × 复杂度热点、对每个 Critical/High finding 做对抗式验证后才写进报告，最后输出单一 `AUDIT.md`——其任务计划**每个任务结尾附一条可直接粘贴的 `/goal` condition**，audit 产出直接接回同一条声明式循环：audit → 任务 → `/goal`。

它与 `/dec` 互补而不重叠——同一条管线，差在触发源与粒度：

| | `/repo-audit` | `/dec` | `/goal` |
|---|---|---|---|
| 角色 | 批量**发现器** | 单任务**合约器** | **执行器** |
| 触发源 | codebase 现状（你还不知道问题在哪） | 你脑中已有的需求 | 拿到 condition 之后 |
| 产出 | `AUDIT.md`：一整个任务队列 | 一份合约 + 一条 condition | 循环到达标 |

Audit 任务已内嵌 `/dec` 的 evaluator 规则，可直接粘进 `/goal`、不必再过一次 `/dec`；日常单发任务仍由 `/dec` 负责。

```
/saygoal:repo-audit                  # 完整 audit → AUDIT.md
/saygoal:repo-audit security         # 可选焦点：某维度或某路径
/saygoal:repo-audit use a workflow   # 大型 repo 可 opt-in 多 agent 编排
```

用普通模式跑（不要 plan mode）、放着让它跑完——全程只读，唯一会创建的文件是 `AUDIT.md`。

## Bilevel 升级 —— arXiv 2603.23420 改了这里的什么

[Bilevel Autoresearch: Meta-Autoresearching Itself](https://arxiv.org/abs/2603.23420) 在 Karpathy 的 autoresearch loop 上再架一圈外圈：读内圈的 trace、找出搜索卡在哪、重写搜索机制本身、验证、失败就回退。论文自己的定位（§5.3）说 Python 代码只是「机制」的载体之一——skill、prompt、workflow 都是等价载体。这对到本 pipeline 刚好一一对应：**`/goal` 是内圈、契约是它的搜索机制、`/dec` 本来就是人工把关的机制设计器**。v4.6.0–v4.8.0 三版补上对照后缺的部分：

| 论文机制 | saygoal 原本就有 | 这几版补上（v4.6.0–v4.8.0） |
|---|---|---|
| 内圈：propose → evaluate → keep/discard | `/goal`（Claude Code / Codex 内置） | — |
| 赛前设计好的机制载体 | 契约；由 `/dec` 编译 | — |
| 骗不过的 evaluator | 「运行 CMD **并贴出输出**」措辞；先查证再输出 | — |
| 结构化搜索 trace | — | **trace 条款**（v4.6.0）：搜索型任务每 5 回合贴一行 search log |
| Tabu Search——论文生成的最强机制 | — | **anti-fixation 条款**（v4.6.0）：验证已两败的做法不得重试 |
| Level 2 外圈：读 trace → 诊断 → 重写机制 | — | **`/saygoal:retro`**（v4.7.0）：五类停滞诊断 → 结构性重写契约 |
| 每次注入都 validate-and-revert | — | **`rollback:` 行**（v4.7.0）：每次重写都附原 condition 原文 |
| 跨 run 持久记忆（EvoScientist 一脉） | — | **`.claude/saygoal.history.jsonl`**（v4.7.0）：retro 写入、`/dec` grilling 先读 |
| Level 1.5 负结果：参数级调整没有增益 | — | retro 的硬规则（v4.7.0）：只准结构性重写——单纯加大回合上限是禁手 |
| Group B 教训：冻结参数把正解墙在外面 | 反投机推导表自动并入约束 | retro 把自动并入的约束列为停滞的**头号嫌疑**（v4.7.0） |
| loop 成本（出自配套的 loop engineering 长文，非论文本身） | 回合上限 | **验证成本感知的上限**（v4.8.0）：验证昂贵就下调上限，或逐回合改跑针对性验证、全套收尾跑 |

> **与本 repo 一贯的诚实原则**：论文的 5× 标题数字是每组 n = 3、标准差达均值的 67%、单一 benchmark，且至少有一位读者回报复现失败。按本 repo 自己 [`EXPERIMENT.md`](./EXPERIMENT.md) 的标准（「任何 N = 3 的 LLM A/B 结论都应视为 uncertain until N ≥ 10」），这个数字当作未经证实。我们采用的是**架构模式**——trace、tabu、外圈重写、validate-and-revert——它们便宜且 fail-safe：非搜索型任务所有条款都不编入，每次重写都自带回退。

## 为什么规则档不是重点 — 实证

`saygoal` 也附一份三行的 `CLAUDE.md`（内容衍生自 [Andrej Karpathy 对 LLM 编码陷阱的观察](https://x.com/karpathy/status/2015883857489522876)）。它是可选的——而 A/B 实证显示规则档几乎不动模型。

在 Opus 4.8 上，抓 bug 率从 **33% 跃升到 90%**，但三组 `CLAUDE.md`（v1／v2／无）**统计上持平**：模型早就把这套纪律内化了，剩下的杠杆只在用户端——也就是 `/dec`。v1 的规则大多早已逐字出现在 Claude Code 的系统提示词里；唯一真正添加的那条（「每一行改动都要对应到请求」）才是 v2 保留下来的。

完整数据、v1→v2 逐字对照与 caveat 都在 [`EXPERIMENT.md`](./EXPERIMENT.md)（英文）。

## 与上游的关系

本仓库是 [`forrestchang/andrej-karpathy-skills`](https://github.com/forrestchang/andrej-karpathy-skills) 的繁体中文（台湾）在地化 fork，为 Claude Code Opus 4.7 → 4.8 时代更新内容。Plugin / marketplace 命名为 `saygoal`；README 为双语（英文 + 繁体中文）。

## 授权

[MIT](./LICENSE) — Copyright © 2026 yelban。

详细出处说明见[与上游的关系](#与上游的关系)章节。
