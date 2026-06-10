---
description: Reframe an imperative request as a declarative /goal contract (success criteria + verification + five-facet boundaries). Outputs a Claude Code /goal condition string. Do not implement yet.
---

<!-- platform: Claude Code (command) · output: single natural-language /goal condition -->
<!-- Running in Codex? Use the seven-field template in plugins/saygoal/skills/dec/SKILL.md instead. -->

`/dec` 是 **declarative** 的縮寫。把下方請求轉成宣告式契約。**不要實作。**

若在 plan mode 被啟動:`/dec` 只分析、不實作、不寫檔——直接輸出契約即可,不要走 ExitPlanMode 送審流程。

---

## 先判斷適用性

任務屬於以下情況,直接回覆「**不適用,建議直接做。**」,不要輸出契約:

- **本質主觀**:UI 風格、文案措辭、命名選擇、視覺微調
- **過於細小**:typo、單行 rename、單一格式變更
- **無可驗證終態**:如「讓它感覺更快」(未給效能門檻)

---

## 輸出格式(適用時)

### 1. 成功條件 (Success criteria)
可驗證的端狀態,且必須是 Claude `/goal` 的 evaluator 在對話 transcript 裡找得到的證據:指令退出碼、輸出比對、可量化門檻(p95 < X ms)。

使用者沒給、由你推定的數字門檻(如 p95 < 200ms),標註 `(assumed,請確認)`——別讓推定值被當成既定需求。

### 2. 驗證指令 (Verification)
> ⚠️ Claude `/goal` 的 evaluator(小模型)**只讀對話 transcript、不自己跑指令、不讀檔案**。

所以驗證一律寫成「**實作時必須執行並貼出輸出**」的形式,並指定可被 pattern-match 的關鍵字串或數字。**禁用** ensure / verify / make sure 這類可被靜態宣告矇混的動詞。

- ✅ `run \`npx playwright test login.spec.ts\` and paste output showing "X passed, 0 failed"`
- ✅ `run \`scripts/bench.sh\` and paste output showing p95 < 200ms`
- ❌ `tests pass` / `the flicker is gone` / `check the file is correct`(evaluator 判不了)

**先查證再輸出**:用唯讀方式確認驗證指令真的可跑(測試檔存在、script 在 package.json 裡、binary 在 PATH)。不存在就標「⚠ 此驗證尚不存在,需先建立」並把建立它列為第一步——否則 `/goal` 第一回合就撞牆。

### 3. 邊界 (Boundaries)
**只列與本任務相關的面,不相關的整塊省略——不要寫「N/A」或「無」。**

- **不可改動**(Constraints):不得更動的行為/語義(public API、認證流程、輸出格式)
- **可改路徑**(Write scope):允許寫 / 禁止碰的路徑
- **外部系統限制**(Action policy):read-only / draft-only / 不得 send·deploy·merge
- **最多幾回合**(預算):Claude 一律加 `or stop after 20 turns`

### 4. Ready-to-use `/goal` condition
合成一條 Claude Code `/goal` 可吃的**自然語言**字串(非結構化欄位)。骨架:

```
[做什麼] until [可量化端狀態,由執行 CMD 並貼出輸出證明]
without [constraints,多條用 AND 串] or stop after 20 turns — adjust by task complexity
```

範例:
```
/goal "run npx playwright test login-flicker.spec.ts until it paste-shows 0 failures
       without modifying src/auth/ or any file outside src/components/LoginPage.tsx
       AND without removing any existing assertion
       or stop after 20 turns"
```

condition 必須**自包含**:禁止「剛剛討論的」「如上所述」這類對話內指涉——這條字串會被複製到全新 session,讀者只看得到它本身。檔名、路徑、門檻全部寫死在字串裡。

### 何時暫停 (Pause-if) — 獨立列出,**不要塞進上面的 condition**
Claude `/goal` 無原生 Pause-if 欄位;塞進 condition 字串 evaluator 會誤判為失敗而繼續 loop。改為:**獨立列出觸發情境,並建議使用者用 Stop hook 實作**(缺權限 / 需破壞性操作 / 需人工決策 / N 次失敗 / 文件衝突)。

---

## 內部規則:反投機推導(依此推導,但**不要把這張表複述給使用者**)

依任務關鍵字自動把對應 constraint 併入「不可改動」。匹配時看語境:動作對象是 UI 元件 / CSS / 暫存物件時,**不**觸發資料層約束。

| 任務關鍵字 | 併入「不可改動」 |
|---|---|
| 效能 / optimize / 加速 / latency / benchmark | without removing any existing feature or test coverage |
| 重構 / refactor / 遷移 / migrate | without changing observable behavior (existing tests must still pass) |
| 測試 / test / CI | without skipping, commenting out, or weakening any existing assertion |
| coverage / 覆蓋率 | without adding trivially-true assertions that inflate the number |
| API / webhook / email / send / deploy / publish(外部系統) | in read-only or draft mode; do not send, deploy, or publish |
| 刪除 / delete / drop(資料、持久層) | pause before any irreversible deletion and surface the target first |
| auth / 認證 / token / permission | do not change the authentication flow or token validation logic |
| 「後續可考慮」「未來再做」「v2」「暫不做但」等**不確定語氣** | 視為非目標,不進成功條件(裸字「未來/可擴展」若屬明確架構要求則不踢) |

---

確認後使用者可:依契約直接實作,或複製 #4 貼入 `/goal` 讓 Claude Code 自動 loop 到達標(需 v2.1.139+)。

---

Request: $ARGUMENTS
