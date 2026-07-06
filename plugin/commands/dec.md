---
description: Reframe an imperative request as a declarative contract (success criteria + verification + five-facet boundaries), distilled into a ready-to-paste Claude Code /goal condition. Do not implement yet.
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

## 適用後、編譯前:先 grill 開放欄位

契約只在「沒有未解問題」時才收斂。動手編之前,先盤出哪些欄位只能靠猜——成功門檻、驗證目標存不存在、可寫邊界、試探性範圍——把它們**問掉**,而不是標 `(assumed)` 帶過。

- **一次只問一題**,每題附上你的建議答案;能用唯讀查碼回答的(測試檔在不在、script 有沒有在 package.json)就查碼,不要問。
- **選項可枚舉的題目用 AskUserQuestion 問**(單選、建議答案放第一個選項並標 `(Recommended)`);自由值題(門檻數字、路徑)也可列 2–3 個建議選項,使用者能用 Other 自填。
- **品味式約束要翻譯成脈絡,不能照抄**:使用者給的是「保持簡單」「別過度設計」「先快速做一版」這類品味式約束時,問出底層原因——這題選項固定,用 AskUserQuestion:**實驗性、可能短命** / **有期限壓力、先求能動** / **長期正式功能**——把答案編進任務脈絡(輸出 #4)。約束只能說「不要做什麼」;脈絡讓實作 agent 自己判斷約束沒預料到的情況。
- **多子項規範多問一題(AskUserQuestion)**:差異報告由誰產生?**實作者自報**(預設、省 token)/ **workflow 獨立驗證**(每個子項派一個獨立驗證 agent,只對照規範與成果、不看實作過程;可信度高但 token 成本明顯較高)。單子項任務不問。答案影響 #5 的 condition 寫法。**子項的判準**:規範裡各自獨立可驗收的交付物才算(不同檔案、功能或驗證方式各一項);同一交付物的多個維度(一張表的多個欄位、一個 script 的多條規則)不算多子項。
- 問完停下等回答,不要在使用者回覆前就吐契約。
- 全部已清楚就跳過、直接編——別對已經夠精確的請求硬問。

**契約 done**:沒有任何裸 `(assumed)`,且每條驗證指令都已查證可跑。問到沒有開放問題,才進入下面的輸出。

---

## 輸出格式(適用時)

### 1. 成功條件 (Success criteria)
可驗證的端狀態,且必須是 Claude `/goal` 的 evaluator 在對話 transcript 裡找得到的證據:指令退出碼、輸出比對、可量化門檻(p95 < X ms)。

使用者沒給的數字門檻(如 p95 < 200ms),**先照上面的 grilling 問**;使用者明確要你自己定,才標 `(assumed,請確認)`——別讓推定值被當成既定需求。

### 2. 驗證指令 (Verification)
> ⚠️ Claude `/goal` 的 evaluator **只讀對話 transcript、不自己跑指令、不讀檔案**。

所以驗證一律寫成「**實作時必須執行並貼出輸出**」的形式,並指定可被 pattern-match 的關鍵字串或數字。**禁用** ensure / verify / make sure 這類可被靜態宣告矇混的動詞。

- ✅ `run \`npx playwright test login.spec.ts\` and paste output showing "X passed, 0 failed"`
- ✅ `run \`scripts/bench.sh\` and paste output showing p95 < 200ms`
- ❌ `tests pass` / `the flicker is gone` / `check the file is correct`(evaluator 判不了)

**先查證再輸出**:用唯讀方式確認驗證指令真的可跑(測試檔存在、script 在 package.json 裡、binary 在 PATH)。不存在就標「⚠ 此驗證尚不存在,需先建立」並把建立它列為第一步——否則 `/goal` 第一回合就撞牆。驗證目標本身就是任務交付物時(如「寫一個 script」),同樣標註並把建立列為第一步即可,不構成矛盾。

**多子項規範 → 逐項差異報告**:成功條件涵蓋多個子項(規範列了好幾條)時,驗證除了指令輸出,再加一條「貼出逐項實作報告:每個子項標 implemented / deviated,deviated 要說明差異」。報告本身是 evaluator 可 pattern-match 的證據,同時堵住「靜默偏離規範」——loop 收斂了但建的不是你要的東西。報告預設由實作者自報;使用者在 grilling 選了 **workflow 獨立驗證**,報告改由驗證 workflow 產生(condition 寫法見 #5)——自報的弱點是自己改的考卷自己打分數,獨立驗證者沒看過實作過程,抓得到自報抓不到的偏離。

### 3. 邊界 (Boundaries)
**只列與本任務相關的面,不相關的整塊省略——不要寫「N/A」或「無」。**

- **不可改動**(Constraints):不得更動的行為/語義(public API、認證流程、輸出格式)
- **可改路徑**(Write scope):允許寫 / 禁止碰的路徑
- **外部系統限制**(Action policy):read-only / draft-only / 不得 send·deploy·merge
- **最多幾回合**(預算):Claude 一律加回合上限;預設 `or stop after 20 turns`,依任務複雜度調整數字

### 4. 任務脈絡 (Context) — 選配,有才寫
一句話說明**為什麼做、任務壽命**:實驗還是正式功能、多久後可能刪、之後誰維護。這是給實作 agent 做判斷用的——約束只能列舉「不要做什麼」,脈絡讓它在約束沒預料到的情況下自己做對決定(「這是實驗,一個月後很可能刪掉——別建丟棄起來會心疼的東西」勝過「保持簡單」)。

只在 grilling 問出內容、或使用者已自己提供時出現;沒有就整節省略,不寫「N/A」。

### 5. Ready-to-use `/goal` condition
合成一條 Claude Code `/goal` 可吃的**自然語言**字串(非結構化欄位)。骨架:

```
[context 一短句,若有 —] [做什麼] until [可量化端狀態,由執行 CMD 並貼出輸出證明]
without [constraints,多條用 AND 串] or stop after [N] turns
```

回合上限 N 預設 20、依任務複雜度調整——這個調整是你(編譯者)的判斷,condition 裡只出現定案的數字,不要把調整說明抄進字串。

有任務脈絡(#4)時,在 condition 開頭放一短句(如 `context: this feature is a throwaway experiment —`),**一句為限**:脈絡是給實作 agent 讀的,evaluator 只 pattern-match until / without 部分,寫長了是雜訊。多子項規範時,在 until 段**最後一個驗證證據之後**併入差異報告要求——自報版:`… and paste a per-item completion report (implemented / deviated, deviations explained)`;grilling 選了 **workflow 獨立驗證**則改為 `… then run a verification workflow (one independent verifier per spec item, judging outcome against the spec) and paste its per-item report (implemented / deviated)`。後者由使用者親手貼進 `/goal`,正好構成 Workflow 工具需要的使用者明確 opt-in,實作 session 可以合法啟用。

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
| 「保持簡單」「別過度設計」「先快速做一版」等**品味式約束** | 不併入「不可改動」——依 grilling 規則問出底層脈絡(實驗?壽命?期限?),編入任務脈絡(#4) |

---

## 契約輸出後:執行通道(偵測 → 詢問 → 派發)

契約輸出後,先偵測可用的委派工具(皆唯讀,失敗視同未安裝):

- **`/codex:rescue`**(openai codex plugin):看本 session 的 available skills 清單有沒有 `codex:rescue`;不確定時備援 `jq -e '.plugins | has("codex@openai-codex")' ~/.claude/plugins/installed_plugins.json`
- **`codex-agent`**(codex-orchestrator):`command -v codex-agent`

**一個都沒偵測到** → 不提委派,只寫:確認後可依契約直接實作,或複製 #5 貼入 `/goal` 讓 Claude Code 自動 loop 到收斂(需 v2.1.139+)。

**偵測到至少一個** → 讀專案偏好檔 `.claude/saygoal.local.json`(格式 `{"delegate": "self-goal" | "codex-rescue" | "codex-agent"}`,不存在就當無偏好),然後用 **AskUserQuestion** 問執行通道——**每次都問,不因偏好跳過**(每次委派都花額度,單次否決權留給使用者);有偏好時把偏好通道排第一個選項標 `(Recommended)`;無偏好時把「自己 `/goal` loop」排第一、同樣標 `(Recommended)`。選項(只列偵測到的):

1. **自己 `/goal` loop**:輸出 #5 讓使用者貼(維持 `/dec` 不實作的邊界)
2. **委派 `/codex:rescue`**:把契約 #1–#4 全文(不含 `/goal` 前綴)交給 Codex 背景執行
3. **委派 `codex-agent`**:同上,適合多份契約平行 fan-out

使用者選定後:

- 選擇與偏好檔不同(或首次)→ 把新偏好寫回 `.claude/saygoal.local.json`;該檔未被 gitignore 時提醒一句(不要擅自改 `.gitignore`)。
- 選 1 → 輸出 #5,結束。
- 選 2 或 3 → **直接派發,不再確認**(剛才的選擇就是確認):選 2 用 **Skill 工具**叫用 `codex:rescue`、args 為 `--background <契約全文>`(不是 Bash);選 3 用 Bash 跑 `codex-agent start "<契約全文>"`。派發後回報 job/thread 資訊與收割方式(`/codex:status`+`/codex:result`,或 `codex-agent await-turn` + `output`),並提醒:收割時照契約 Verification 驗收、多子項看差異報告——只讀最終輸出,過程不回灌。

委派是**調度**,不違反本 command 的「不要實作」:實作發生在被委派的模型,且以使用者當下的明確選擇為前提。

---

Request: $ARGUMENTS
