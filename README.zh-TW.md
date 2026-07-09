# saygoal

> **說出目標，看著它達成**——給 Claude Code 與 Codex 的宣告式 `/dec` + `/goal`，延續 Karpathy「給成功條件，然後看著它跑」的精神。

![/dec — 從命令式轉宣告式](./saygoal.TW.png)

[English](./README.md) | 繁體中文（台灣） | [简体中文](./README.zh-CN.md) | [日本語](./README.ja.md)

> **主要 repo**：[`aeopress/saygoal.TW`](https://github.com/aeopress/saygoal.TW)（原於 [`yelban/andrej-karpathy-skills.TW`](https://github.com/yelban/andrej-karpathy-skills.TW) 維護，現已封存）

## 這是什麼

`saygoal` 把模糊的命令式請求轉成**可驗證的契約**，再讓 agent 自己 loop 到契約達成：

- **`/dec <任務>`** 把你的任務改寫成成功條件 + 驗證指令 + 邊界，並產出一條可直接貼上的 **`/goal` condition**。
- 把它貼進 Claude Code（或 Codex）內建的 **`/goal`**——一個小快模型每 turn 檢查 transcript，盯著 agent 做到條件成立為止。
- **`/saygoal:retro`**——`/goal` loop 停滯時，把 transcript 當搜尋 trace 讀、診斷卡點，結構性重寫契約（修訂版 condition＋一行 rollback）。

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

**先問清楚，再編譯（grilling 前置）**：好契約要能收斂，前提是沒有未解問題。所以面對模糊請求，`/dec` 會在編譯前先 grill——一次只問一題、每題附上建議答案，把只能靠猜的欄位（門檻、驗證目標存不存在、可寫邊界）問掉，而不是默默標 `(assumed)` 帶過。三種行為一目了然：**模糊任務** → 一次一題、問到收斂；**太主觀或太小** → 回「不適用，建議直接做」；**清楚且夠份量** → 不囉嗦、直接編出契約。skip-when-clear 護欄讓它只在真正需要時才追問，不騷擾已經精確的請求（行為已用 Codex CLI 實測通過）。Claude Code 團隊成員 Thariq 描述的 Fable 5 工作法正是這個流程——"I'd ask Claude to interview me about the implementation before writing the final spec file"（[來源影片](https://x.com/trq212/status/2073100352921215386)）。

**給脈絡，不只給約束（context, not constraints）**：Thariq 影片裡最精華的一招——與其說「保持簡單、別過度設計」，不如說「這是實驗功能，一個月後很可能刪掉，別建丟棄起來會心疼的東西」。約束只能列舉「不要做什麼」；脈絡讓 agent 在約束沒預料到的情況下自己做對決定。所以 `/dec` 遇到品味式約束不會照抄進契約，而是 grill 出底層原因（實驗？壽命？期限？——這題選項固定，Claude 版用 AskUserQuestion 單選），編成契約的選配「任務脈絡（Context）」欄位——Claude 版以一短句帶進 `/goal` condition 開頭（evaluator 只判 until / without 部分，脈絡是給實作 agent 讀的），Codex 版是七欄位外的選配 `Context:` 行。

**多子項規範 → 逐項差異報告**：規範列了多個子項時，契約會把驗證延伸為「貼出逐項實作報告：每項標 implemented / deviated 並說明差異」——對應 Thariq 的 "prepare a report on what was implemented and if anything differed"。報告是 evaluator 可 pattern-match 的證據，也堵住最隱蔽的失敗模式：loop 收斂了，但建的不是你要的東西。報告預設由實作者自報；Claude 版在多子項時 grilling 會多問一題，可升級為 **workflow 獨立驗證**——每個子項派一個獨立驗證 agent、只對照規範與成果、不看實作過程——正是 Thariq 的 "use a workflow to verify each part of the plan"。獨立驗證可信（自報是自己改考卷）但較花 token，所以做成選項、預設自報。

**搜尋型任務 → 收斂護欄**：任務要靠多輪「嘗試→驗證→再嘗試」才收斂（效能調校、flaky test 除錯、追 benchmark 數字）時，loop 的典型死法是同狀態下重提同一改法、連續失敗到回合上限——LLM 退回自身 priors。這正是 [Bilevel Autoresearch](https://arxiv.org/abs/2603.23420) 在 Karpathy 自己的 pretraining benchmark 上記錄到的失敗模式，而它的解法——打破內圈的固定搜尋模式——搬到 `/dec` 上就是以契約為機制載體：編譯出的 condition 會多兩條護欄——until 段的 **trace 條款**（`pasting every 5 turns a one-line search log: approaches tried → result → ruled out`），讓 transcript 保持可診斷的搜尋紀錄；without 段的 **anti-fixation 條款**（`without repeating an approach whose verification output has already failed twice`），相當於論文 Tabu Search 機制的 prompt 版。非搜尋型任務兩條都不加：在那裡它們是雜訊。

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
5. loop 停滯？/saygoal:retro       ← 讀 trace、重寫契約（外圈）
```

### loop 停滯時 —— `/saygoal:retro`，外圈

`/goal` loop 可能停滯：撞到 `or stop after 20 turns` 時還在重提同一失敗修法的變體。把原 condition 直接重掛是唯一保證沒用的一招——[Bilevel Autoresearch](https://arxiv.org/abs/2603.23420) 的消融實驗裡，參數級調整沒有可靠增益，整個 5× 效果都來自機制級重寫。`/saygoal:retro` 就是這條 pipeline 的外圈：把停滯 session 的 transcript 當搜尋 trace 讀，判定停滯類別——驗證斷裂、門檻不可達、邊界牆住正解（自動併入的約束列頭號嫌疑）、固著、範圍錯置——然後結構性重寫契約。輸出是一條可直接貼上的修訂版 condition，外加一行 `rollback:` 照抄原版——壞的重寫最多只花你一次貼上。每次 retro 還會在 `.claude/saygoal.history.jsonl` 補一行紀錄，之後的 `/dec` grilling 會先讀它——過去的停滯原因變成下一份契約的前置查證。

### 契約也是委派 prompt —— 與 Codex 委派工具協作

`/dec` 的輸出不只能餵 `/goal`。一份好的委派 prompt 需要五件事——context、明確目標、約束、輸出格式、完成判準——而這正好是契約的欄位。所以同一份契約也可以整段（不含 `/goal` 前綴）直接當作委派 prompt：

- **[openai/codex-plugin-cc](https://github.com/openai/codex-plugin-cc)**（`/codex:rescue`）：`/dec` 先把模糊需求編成契約，再 `/codex:rescue --background <契約全文>` 丟給 Codex 背景執行。收割（`/codex:result`）時照契約的驗證欄位驗收；逐項差異報告讓你只讀最終輸出就能判斷有沒有偏離，不用回看過程。
- **[codex-orchestrator](https://github.com/yelban/codex-orchestrator)**（`codex-agent` CLI）：平行 fan-out 多個任務時，每個 `codex-agent start "<契約>"` 都帶著自己的驗證與邊界；`await-turn` 收割後照 Verification 驗收即可。

Claude 版的 `/dec` 會把這件事自動化：契約輸出後偵測這兩個工具（看 session 的 skills 清單、`command -v codex-agent`），偵測到就用 AskUserQuestion 問執行通道——自己 `/goal` loop，還是委派出去。你的選擇記在專案的 `.claude/saygoal.local.json`，下次排在第一個選項；但**每次仍會問**（每次委派都花額度，單次否決權留在你手上）。選了委派就當場背景派發，收割時照契約的驗證欄位驗收。都沒安裝就不會提委派，行為與從前相同。

分工是上下游：`/dec` 管「契約寫得夠不夠收斂」，委派工具管「誰去執行、怎麼平行」。同一份契約，貼 `/goal` 是自己 loop 到綠燈，交給委派工具是外包給另一顆模型——驗收標準不變。

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

> **從舊版升級？** 本專案前身是 `andrej-karpathy-skills.TW`（marketplace 名 `karpathy-skills`，舊 repo 已封存）。若你在改名前裝過，先移除舊 marketplace，否則收不到更新。`marketplace remove` 會一併解除安裝舊 plugin：
>
> ```
> /plugin marketplace remove karpathy-skills
> /plugin marketplace add aeopress/saygoal.TW
> /plugin install saygoal@saygoal
> /reload-plugins
> ```

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

## 加碼指令：`/saygoal:repo-audit`

Plugin 也附帶 `/saygoal:repo-audit`——principal 等級的唯讀 repo audit（改編自 [OmerFarukOruc 的 `/repo-audit` gist](https://gist.github.com/OmerFarukOruc/753f95b1ac278b683be83ed26b3bcc1f)，為 saygoal 工作流調校）。它會先畫出 repo map，再按 audit 維度並行展開 subagents、挖 git 歷史找 churn × 複雜度熱點、對每個 Critical/High finding 做對抗式驗證後才寫進報告，最後輸出單一 `AUDIT.md`——其任務計畫**每個任務結尾附一條可直接貼上的 `/goal` condition**，audit 產出直接接回同一條宣告式迴圈：audit → 任務 → `/goal`。

它與 `/dec` 互補而不重疊——同一條管線，差在觸發源與粒度：

| | `/repo-audit` | `/dec` | `/goal` |
|---|---|---|---|
| 角色 | 批次**發現器** | 單任務**合約器** | **執行器** |
| 觸發源 | codebase 現況（你還不知道問題在哪） | 你腦中已有的需求 | 拿到 condition 之後 |
| 產出 | `AUDIT.md`：一整個任務佇列 | 一份契約 + 一條 condition | 迴圈到達標 |

Audit 任務已內嵌 `/dec` 的 evaluator 規則，可直接貼進 `/goal`、不必再過一次 `/dec`；日常單發任務仍由 `/dec` 負責。

```
/saygoal:repo-audit                  # 完整 audit → AUDIT.md
/saygoal:repo-audit security         # 可選焦點：某維度或某路徑
/saygoal:repo-audit use a workflow   # 大型 repo 可 opt-in 多 agent 編排
```

用一般模式跑（不要 plan mode）、放著讓它跑完——全程唯讀，唯一會建立的檔案是 `AUDIT.md`。

## 為什麼規則檔不是重點 — 實證

`saygoal` 也附一份三行的 `CLAUDE.md`（內容衍生自 [Andrej Karpathy 對 LLM 編碼陷阱的觀察](https://x.com/karpathy/status/2015883857489522876)）。它是可選的——而 A/B 實證顯示規則檔幾乎不動模型。

在 Opus 4.8 上，抓 bug 率從 **33% 躍升到 90%**，但三組 `CLAUDE.md`（v1／v2／無）**統計上持平**：模型早就把這套紀律內化了，剩下的槓桿只在使用者端——也就是 `/dec`。v1 的規則大多早已逐字出現在 Claude Code 的系統提示詞裡；唯一真正新增的那條（「每一行改動都要對應到請求」）才是 v2 保留下來的。

完整資料、v1→v2 逐字對照與 caveat 都在 [`EXPERIMENT.md`](./EXPERIMENT.md)（英文）。

## 與上游的關係

本倉庫是 [`forrestchang/andrej-karpathy-skills`](https://github.com/forrestchang/andrej-karpathy-skills) 的繁體中文（台灣）在地化 fork，為 Claude Code Opus 4.7 → 4.8 時代更新內容。Plugin / marketplace 命名為 `saygoal`；README 為雙語（英文 + 繁體中文）。

## 授權

[MIT](./LICENSE) — Copyright © 2026 yelban。

詳細出處說明見[與上游的關係](#與上游的關係)章節。
