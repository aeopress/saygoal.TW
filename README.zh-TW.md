# saygoal

> **說出目標，看著它達成**——給 Claude Code 與 Codex 的宣告式 `/dec` + `/goal`，延續 Karpathy「給成功條件，然後看著它跑」的精神。

![/dec — 從命令式轉宣告式](./saygoal.TW.png)

[English](./README.md) | 繁體中文（台灣） | [简体中文](./README.zh-CN.md) | [日本語](./README.ja.md)

> **主要 repo**：[`aeopress/saygoal.TW`](https://github.com/aeopress/saygoal.TW)（原於 [`yelban/andrej-karpathy-skills.TW`](https://github.com/yelban/andrej-karpathy-skills.TW) 維護，現已封存）

## 這是什麼

`saygoal` 把模糊的命令式請求轉成**可驗證的契約**，再讓 agent 自己 loop 到契約達成：

- **`/dec <任務>`** 把你的任務改寫成成功條件 + 驗證指令 + 邊界，並產出一條可直接貼上的 **`/goal` condition**。
- 把它貼進 Claude Code（或 Codex）內建的 **`/goal`**——一個小快模型每 turn 檢查 transcript，盯著 agent 做到條件成立為止。

**30 秒範例：**

```
/dec 修登入頁第一次載入時的閃爍

→ /goal "run npx playwright test login-flicker.spec.ts until it paste-shows 0 failures
         without changing the auth flow or any file outside the login component
         or stop after 20 turns"
```

`/dec` 寫契約；`/goal` 跑到綠燈。支援 **Claude Code**（`/dec` command）與 **OpenAI Codex**（`$dec` skill — 七欄位格式）。

→ [安裝](#安裝) · [運作原理](#dec--goal--工作流) · [為什麼規則檔不是重點](#為什麼規則檔不是重點--實證)

## `/dec` + `/goal` — 工作流

Karpathy 最強的洞見其實是**使用者端的紀律**，不是 LLM 自我約束的事：

> 「LLM 非常擅長循環執行直到達成特定目標⋯⋯不要告訴它該做什麼，給它成功標準然後看著它跑完。」

兩個 slash command 剛好對應 Karpathy 那句「給成功條件 + 看著它跑」的**兩個動詞**：

| | `/dec`（本倉庫） | `/goal`（Claude Code 內建，v2.1.139+） |
|---|---|---|
| 階段 | **動手前**：把模糊請求改寫成契約 | **動手中**：盯著 Claude 跑直到契約達成 |
| 動作 | 重寫使用者輸入、**不動手** | 每 turn 後讓小模型評估是否達標、沒達標自動進下一 turn |
| 持久度 | 一次性轉換、等你確認 | Session-scoped、直到 `/goal clear` |
| 評估者 | **你**（人工 review 契約） | **Haiku**（讀 transcript 自動判 yes/no） |
| Karpathy 動詞 | "give it success criteria" | "watch it go" |

### 何時宣告式勝過命令式

| 命令式（槓桿弱） | 宣告式（槓桿強） |
|---|---|
| 「加上輸入驗證」 | 「為這些無效輸入寫失敗測試，然後讓它們通過」 |
| 「修這個 bug」 | 「寫一個能重現 bug 的測試，然後讓它通過 — 其他測試必須還能過」 |
| 「讓它更快」 | 「把這個負載下的 p95 延遲壓到 X ms 以下；用 `scripts/bench.sh` 量」 |
| 「重構 X」 | 「重構 X 但不能改變可觀察行為；既有測試必須還能過」 |

- **宣告式**：有可觀察結果的功能、bug 修復、效能工作、有測試覆蓋的重構。
- **命令式**（跳過 `/dec`）：探索性編輯、UI 微調、文字創作、任何「完成」標準主觀的工作。

連同目標一起給 agent 驗證手段：測試指令、benchmark 腳本、lint 指令、給視覺檢查的 browser MCP。然後放手讓它迭代。

### 單獨用 `/dec`

`dec` 是 **declarative**（宣告式）的縮寫。指令把命令式需求改寫成契約；你確認後才會動工。

```
/dec 修登入頁第一次載入時的閃爍
```

回覆會給你成功條件（例如「Playwright 截圖比對 10 次、位移 < 2px」）、一條措辭成「Claude 必須實際執行並貼出輸出」的驗證指令、以及按需出現的邊界（不可改動 / 可寫路徑 / 外部系統限制）——**外加一條可直接複製貼上的 `/goal` condition**（自然語言的 `[做什麼] until [端狀態] without [約束] or stop after 20 turns` 句式）。若任務太主觀或太小，會回「不適用，建議直接做」、不硬轉換。適合單一 prompt 套用宣告式紀律、不需要自主迭代的場合（或在 Cursor / 舊版 Claude Code 沒有 `/goal` 時）。

### `/dec` 當作 `/goal` 的「邊界設定器」

`/goal` 的效果完全取決於你給它的 condition 字串。寫不好的 condition 永遠不會收斂：

```
❌ /goal "登入頁不要閃爍"
   Haiku 怎麼判定「不閃爍」？看截圖？讀 console？
   結果 evaluator 一律回 yes 或一律回 no、loop 永遠不收斂。

✅ /dec 修登入頁第一次載入時的閃爍
   →  成功條件：Playwright 截圖比對 10 次、位移 < 2px
       驗證指令：執行 `npx playwright test login-flicker.spec.ts` 並貼出顯示 0 failures 的輸出
       邊界：寫入限定在登入元件；不動 auth 流程

✅ /goal "run npx playwright test login-flicker.spec.ts until it paste-shows 0 failures
          without changing the auth flow or any file outside the login component
          or stop after 20 turns"
   Haiku 讀 transcript 內貼出的測試輸出能精準判定。
   Loop 真的會收斂。
```

`/dec` 強制設定 `/goal` 自己給不出的三件事：

1. **可機器判定的成功條件**——「diff < 2px」「10 passed」「p95 < X ms」evaluator 看 transcript 就能 yes/no
2. **嵌進契約的驗證指令**——強迫 Claude 真的去跑檢查、而不是靜態推理然後回報「應該可以了」（這正是我們 T4 declarative-loop 測試看到的失敗模式）
3. **結構化邊界（五面、按需）**——不可改動、可寫路徑、外部系統限制、何時暫停、回合上限。對 Claude 這些會編進 condition（「… without test files changed and no new files in src/legacy/, or stop after 20 turns」）；其中「何時暫停」單獨列出、建議用 Stop hook，因為 evaluator 判不了它。

### 完整 pipeline

```
1. /dec <模糊需求>                 ← 契約 + 一條編好的 /goal condition
2. 你 review 契約                  ← 人類確認方向
3. 複製 #1 那條 /goal 指令貼上     ← Haiku 接手當判官
4. Claude 自主 loop 到收斂          ← Karpathy 說的「watch it go」
```

### Codex `/goal` 也適用

OpenAI 的 Codex CLI 比 Claude Code 早 11 天，在 [v0.128.0（2026-04-30）](https://developers.openai.com/codex/cli/slash-commands) 推出自家的 `/goal`。Codex [官方 goal 寫法指南](https://developers.openai.com/codex/use-cases/follow-goals)列出好的 goal 應該明確的四件事：

> "what Codex should achieve, what it shouldn't change, how it should validate progress, and when it should stop"

並明確指出 **"Codex should know what 'done' means before it starts."** 這正是 `/dec` 寫出來的契約：

| Codex docs 要求 | `/dec` 對應輸出（Codex 七欄位） |
|---|---|
| what Codex should achieve | **Outcome** |
| what it shouldn't change | **Constraints + Boundaries** |
| how it should validate progress | **Verification** |
| when it should stop | **Stop when + Pause if** |

開 Codex `/goal` 之前先跑 `dec` 的三個 confirmed value：

1. **你不用記 Codex 那條 checklist**——`/dec` 的 template 每次都把七個 Codex 欄位（outcome、verification、constraints、boundaries、iteration policy、stop、pause）填滿。
2. **`/dec` 要求每個欄位都可量測**——[`plugin/commands/dec.md`](./plugin/commands/dec.md) 要求「可驗證的端狀態，且必須是 `/goal` 的 evaluator 在 transcript 裡找得到的證據：指令退出碼、輸出比對、可量化門檻」。Codex docs 雖然主張 goal 應該可測試，但沒附樣板在 user 端強制執行這件事。
3. **`/dec` 對主觀任務的「不適用，建議直接做」short-circuit**（UI 微調、文案、單行 rename）—— Codex `/goal` 沒有 documented 等價功能。對主觀任務開 `/goal` 正是 Codex docs 警告的：**"Avoid using a goal for a loose list of unrelated work."**

**`dec` 與 Codex 搭配使用**：本倉庫也提供 Codex 版的 `dec` skill（透過 Codex plugin 打包，位於 [`plugins/saygoal`](./plugins/saygoal)），輸出 Codex 的七欄位 `/goal` 模板（Claude command 則輸出單一條自然語言 condition——兩邊各自產出宿主的原生格式）。在 Codex CLI 可用 `$dec <request>` 叫用，或透過 `/skills` 選取；它輸出的 `/goal` 區塊可以直接貼到 Codex `/goal "..."`。這不會改變 Claude Code 的 `/dec`：原本的 command 仍在 [`plugin/commands/dec.md`](./plugin/commands/dec.md)，也仍然使用 Claude 的 `$ARGUMENTS` template。

> **Caveat——這是設計層面的聲明、不是實證。** 我們**沒有**對 `/dec` + Codex `/goal` 跑控制組實驗。上面的對應是讀 `/dec` 的 prompt template 對照 Codex [published goal-writing guidance](https://developers.openai.com/codex/use-cases/follow-goals) 推得。[`EXPERIMENT.md`](./EXPERIMENT.md) 那個 N=40 A/B 測的是 CLAUDE.md 對 Opus 4.7 的效應、不是 `/dec` 本身。

> **呼叫名稱注意**：透過外掛（選項 A）安裝時，Claude Code 會把指令 namespace 成 `/saygoal:dec`。想要短的 `/dec`，請用選項 C 手動安裝。內建的 `/goal` 不受安裝方式影響、永遠可用。

> **`/goal` 評估者注意**：`/goal` 把每 turn 的 transcript 餵給 Claude Code 內建的「small fast model」slot、[預設是 Haiku](https://code.claude.com/docs/en/goal.md)。**沒有 `/goal` 專屬的 model 設定**；唯一替換方式是用 `ANTHROPIC_DEFAULT_HAIKU_MODEL` 環境變數整體 redirect 那個 slot（[model config 文件](https://code.claude.com/docs/en/model-config.md)）——但這會把 `haiku` alias 全部換掉、不只 `/goal`。一般使用不需動。

## 安裝

### Claude Code

```
/plugin marketplace add aeopress/saygoal.TW
/plugin install saygoal@saygoal
```

裝好後用 `/saygoal:dec <任務>`。內建 `/goal` 永遠可用、不需安裝。

### Codex

clone 本 repo 後、在 root 執行：

```
codex plugin marketplace add .
codex plugin add saygoal@saygoal
```

用 `$dec <任務>`（或從 `/skills` 選），再把產出的 `/goal "..."` 貼進 Codex 內建 `/goal`。

<details>
<summary><b>進階</b> — 短 <code>/dec</code>、可選的 <code>CLAUDE.md</code> 規則、自動更新、Cursor</summary>

**短 `/dec`（免 namespace）。** 外掛會把指令 namespace 成 `/saygoal:dec`。想要短的 `/dec`，把指令檔放到全域：

```bash
mkdir -p ~/.claude/commands
curl -o ~/.claude/commands/dec.md \
  https://raw.githubusercontent.com/aeopress/saygoal.TW/main/plugin/commands/dec.md
```

**三條 `CLAUDE.md` 規則（可選）。** 我們的 [A/B 實證](./EXPERIMENT.md) 顯示對 Opus 4.7/4.8 沒有可測量效應——想要才裝：

```bash
curl -o CLAUDE.md https://raw.githubusercontent.com/aeopress/saygoal.TW/main/CLAUDE.md
# 或只把規則追加到既有 CLAUDE.md：
# curl -s https://raw.githubusercontent.com/aeopress/saygoal.TW/main/CLAUDE.md | sed -n '/^## Stop when confused/,$p' >> CLAUDE.md
```

**自動更新的短 `/dec`。** clone 一次再 symlink，`git pull` 就會保持最新：

```bash
mkdir -p ~/.claude/external ~/.claude/commands
git clone https://github.com/aeopress/saygoal.TW ~/.claude/external/saygoal.TW
ln -sf ~/.claude/external/saygoal.TW/plugin/commands/dec.md ~/.claude/commands/dec.md
# 之後更新：cd ~/.claude/external/saygoal.TW && git pull
```

**Cursor。** 本倉庫附 [`.cursor/rules/karpathy-guidelines.mdc`](.cursor/rules/karpathy-guidelines.mdc)（`alwaysApply: true`）；詳情見 [`CURSOR.md`](./CURSOR.md)。

</details>

## 為什麼規則檔不是重點 — 實證

`saygoal` 也附一份三行的 `CLAUDE.md`（內容衍生自 [Andrej Karpathy 對 LLM 編碼陷阱的觀察](https://x.com/karpathy/status/2015883857489522876)）。它是可選的——而 A/B 實證顯示規則檔幾乎不動模型。

在 Opus 4.8 上，抓 bug 率從 **33% 躍升到 90%**，但三組 `CLAUDE.md`（v1／v2／無）**統計上持平**：模型早就把這套紀律內化了，剩下的槓桿只在使用者端——也就是 `/dec`。v1 的規則大多早已逐字出現在 Claude Code 的系統提示詞裡；唯一真正新增的那條（「每一行改動都要對應到請求」）才是 v2 保留下來的。

完整資料、v1→v2 逐字對照與 caveat 都在 [`EXPERIMENT.md`](./EXPERIMENT.md)（英文）。

## 與上游的關係

本倉庫是 [`forrestchang/andrej-karpathy-skills`](https://github.com/forrestchang/andrej-karpathy-skills) 的繁體中文（台灣）在地化 fork，為 Claude Code Opus 4.7 → 4.8 時代更新內容。Plugin / marketplace 命名為 `saygoal`；README 為雙語（英文 + 繁體中文）。

## 授權

[MIT](./LICENSE) — Copyright © 2026 yelban。

詳細出處說明見[與上游的關係](#與上游的關係)章節。
