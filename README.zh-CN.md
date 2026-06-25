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

**先问清楚，再编译（grilling 前置）**：好契约要能收敛，前提是没有未解问题。所以面对模糊请求，`/dec` 会在编译前先 grill——一次只问一题、每题附上建议答案，把只能靠猜的字段（门槛、验证目标存不存在、可写边界）问掉，而不是默默标 `(assumed)` 带过。三种行为一目了然：**模糊任务** → 一次一题、问到收敛；**太主观或太小** → 回「不适用，建议直接做」；**清楚且够分量** → 不啰嗦、直接编出契约。skip-when-clear 护栏让它只在真正需要时才追问，不骚扰已经精确的请求（行为已用 Codex CLI 实测通过）。

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

clone 本 repo 后、在 root 运行：

```
codex plugin marketplace add .
codex plugin add saygoal@saygoal
```

用 `$dec <任务>`（或从 `/skills` 选），再把产出的 `/goal "..."` 贴进 Codex 内置 `/goal`。

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

## 为什么规则档不是重点 — 实证

`saygoal` 也附一份三行的 `CLAUDE.md`（内容衍生自 [Andrej Karpathy 对 LLM 编码陷阱的观察](https://x.com/karpathy/status/2015883857489522876)）。它是可选的——而 A/B 实证显示规则档几乎不动模型。

在 Opus 4.8 上，抓 bug 率从 **33% 跃升到 90%**，但三组 `CLAUDE.md`（v1／v2／无）**统计上持平**：模型早就把这套纪律内化了，剩下的杠杆只在用户端——也就是 `/dec`。v1 的规则大多早已逐字出现在 Claude Code 的系统提示词里；唯一真正添加的那条（「每一行改动都要对应到请求」）才是 v2 保留下来的。

完整数据、v1→v2 逐字对照与 caveat 都在 [`EXPERIMENT.md`](./EXPERIMENT.md)（英文）。

## 与上游的关系

本仓库是 [`forrestchang/andrej-karpathy-skills`](https://github.com/forrestchang/andrej-karpathy-skills) 的繁体中文（台湾）在地化 fork，为 Claude Code Opus 4.7 → 4.8 时代更新内容。Plugin / marketplace 命名为 `saygoal`；README 为双语（英文 + 繁体中文）。

## 授权

[MIT](./LICENSE) — Copyright © 2026 yelban。

详细出处说明见[与上游的关系](#与上游的关系)章节。
