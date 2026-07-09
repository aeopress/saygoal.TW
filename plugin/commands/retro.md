---
description: Post-mortem a stalled /goal loop — read the transcript as a search trace, diagnose the stall class, and structurally rewrite the contract into a revised /goal condition with a rollback line. Does not implement.
argument-hint: [optional — paste the original /goal condition and the last few verification outputs if the loop ran in another session]
---

<!-- platform: Claude Code (command) · output: stall diagnosis + revised /goal condition · only writable file: .claude/saygoal.history.jsonl -->
<!-- the outer loop of the saygoal pipeline: /dec compiles the mechanism, /goal runs the inner loop, /retro rewrites the mechanism when the inner loop stalls (Bilevel Autoresearch, arXiv:2603.23420) -->

`/retro` 是 `/goal` loop 的**外圈**:內圈撞回合上限未收斂、或明顯空轉時,把 transcript 當 trace 讀、診斷停滯類別、**結構性重寫契約**。不繼續實作任務本身;唯一可寫的檔案是 `.claude/saygoal.history.jsonl`。

---

## 輸入

- **同 session**(預設):loop 就在本對話跑過,直接讀 transcript——原 condition、每回合的嘗試與驗證輸出、trace 條款留下的 search log。
- **跨 session**:請使用者貼上原 `/goal` condition 與最後幾回合的驗證輸出(或 search log)。兩樣缺一就停下來要,不要憑空診斷。

---

## Step 1 — 重建 trace

從 transcript 抽出:原 condition(until / without / turn cap)、逐回合「改了什麼 → 驗證輸出 → evaluator 判定」、重複出現的模式。契約有 trace 條款(見 /dec 收斂護欄)時直接用 search log,省掉重建。

## Step 2 — 診斷停滯類別(至少一類,可複選;每類都要附 transcript 證據)

| 類別 | transcript 訊號 |
|---|---|
| **驗證斷裂** | 驗證指令跑不動/目標不存在;或輸出格式與 condition 的 pattern 對不上——與實作內容無關地每回合都失敗,或每回合都輕鬆過 |
| **門檻不可達** | 多個**不同**方向的嘗試都逼近但未達門檻 |
| **邊界牆住正解** | 證據指向的方向正好被某條 without 條款擋住——**反投機推導自動併入的約束列頭號嫌疑**,使用者原話的約束次之 |
| **固著** | 同一做法(或同義改寫)重試 ≥3 次、驗證輸出相同——內圈退回自身 priors |
| **範圍錯置** | 多數回合在做與端狀態無關的事——任務被誤解 |

## Step 3 — 結構性重寫(對應診斷)

只調參數(加大回合上限、附「請多試別的方向」指引)**無效**——這是 Bilevel Autoresearch 的 Level 1.5 負結果:指引式介入沒有可靠增益,有效的是改變機制本身。重寫必須動到契約結構:

- **驗證斷裂** → 先修驗證:缺的 test/script 列為修訂契約的第一步建立;或改寫 until 段的 pattern,使其對得上驗證指令的真實輸出格式
- **門檻不可達** → 用 AskUserQuestion 與使用者重議門檻(附建議值與 transcript 依據),或拆成階段契約——先收斂做得到的 X,再另開一條 `/goal` 攻 Y
- **邊界牆住正解** → 鬆綁該條款:反投機自動加的,直接改並在輸出標明;使用者原話的約束,AskUserQuestion 確認後才動
- **固著** → 併入 anti-fixation 條款(見 /dec 收斂護欄),並把已排除方向寫進 context 前綴:`context: X and Y already failed verification — search elsewhere —`
- **範圍錯置** → 契約層級救不了,回 `/dec` 重新 grill;本命令只輸出診斷,不硬編修訂版

## Step 4 — 輸出

1. **停滯診斷**:類別 + 證據(第幾回合、重複了什麼)
2. **修訂欄位**:只列動過的欄位與理由,沒動的不重抄
3. **修訂版 `/goal` condition**:自包含、遵守 `/dec` 的 evaluator 規則(執行 CMD 並貼出輸出、指定可 pattern-match 的字串、禁用 ensure/verify/make sure)
4. **rollback 行**:原 condition 原文照抄、前綴 `rollback:`——修訂版跑得更差時貼回原版,壞的重寫最多只花你一次貼上(validate-and-revert)
5. **寫入歷史**:append 一行到 `.claude/saygoal.history.jsonl`:`{"date":"YYYY-MM-DD","task":"<一句話>","outcome":"stalled","stall_class":"<類別>","resolution":"<改了什麼>"}`——之後 `/dec` grilling 會先讀它,把同類任務的停滯原因變成下次的前置查證。該檔未被 gitignore 時提醒一句(不要擅自改 `.gitignore`)。

---

Stalled loop: $ARGUMENTS
