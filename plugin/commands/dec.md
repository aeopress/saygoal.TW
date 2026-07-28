---
description: Reframe an imperative request as a declarative contract (success criteria + verification + five-facet boundaries), distilled into a ready-to-paste Claude Code /goal condition. Do not implement yet.
---

<!-- platform: Claude Code (command) · output: single natural-language /goal condition -->
<!-- Running in Codex? Use the seven-field template in plugins/saygoal/skills/dec/SKILL.md instead. -->

`/dec` 是 **declarative** 的縮寫。把下方請求轉成宣告式契約。**不要實作**——在 plan mode 也一樣:只輸出契約,不走 ExitPlanMode 送審。

---

## 總綱:契約的三個讀者

以下規則全是為三個讀者服務的推論;遇到規則沒涵蓋的情況,回到讀者的限制自行判斷:

- **`/goal` evaluator(Haiku)**:只讀對話 transcript,不自己跑指令、不讀檔案,只能 pattern-match。要它判定的證據,必須以「實作時執行 CMD 並貼出輸出」的形式出現在 transcript 裡,並指定可比對的字串或數字;ensure / verify / make sure 這類可被靜態宣告矇混的動詞它判不了,禁用。
- **實作 agent**:可能是另一個模型、可能在收斂壓力下走捷徑。契約條款是護欄,不是教學——邊界防的是 loop 誘發的投機(弱化測試、刪功能保綠燈),不是模型不懂。
- **使用者**:契約是他確認方向的介面;condition 會被貼進全新 session,必須 self-contained——檔名、路徑、門檻內嵌,no deictic references。

---

## 先判斷適用性

任務屬於以下情況,直接回覆「**不適用,建議直接做。**」,不要輸出契約:

- **本質主觀**:UI 風格、文案措辭、命名選擇、視覺微調
- **過於細小**:typo、單行 rename、單一格式變更
- **無可驗證終態**:如「讓它感覺更快」(未給效能門檻)

---

## 適用後、編譯前:先 grill 開放欄位

契約只在沒有未解問題時才收斂。動手編之前,把只能靠猜的欄位——成功門檻、驗證目標存不存在、可寫邊界、試探性範圍——**問掉**,而不是標 `(assumed)` 帶過。

- 專案存在 `.claude/saygoal.invariants.md`(恆定邊界:不可碰路徑、量尺路徑、外部系統政策)時先讀,對應面直接併入 #3、不再重問;grilling 問出使用者標明「每個任務都一樣」的邊界時,提議寫入該檔(經同意)。
- 專案存在 `.claude/saygoal.history.jsonl`(`/saygoal:retro` 的停滯紀錄與 `/saygoal:judge` 的驗收判決)時先讀:同類任務先前的停滯原因、被抓過的造假手法,直接列為本次先查證或先問的項目。
- 一次只問一題並附建議答案;選項可枚舉的題目用 AskUserQuestion。能用唯讀查碼回答的(測試檔在不在、script 有沒有在 package.json)就查碼,不要問。
- **品味式約束翻譯成脈絡,不照抄**:「保持簡單」「別過度設計」「先快速做一版」這類話,問出底層原因(固定選項:**實驗性、可能短命** / **有期限壓力、先求能動** / **長期正式功能**),編進任務脈絡(#4)。約束只能枚舉禁止事項;脈絡是 commander's intent。
- **多子項規範多問一題**:差異報告由誰產生——**實作者自報**(預設、省 token)/ **workflow 獨立驗證**(每子項一個獨立驗證 agent,只對照規範與成果、不看實作過程;可信度高但 token 成本明顯較高)。子項的判準:各自獨立可驗收的交付物才算(不同檔案、功能或驗證方式各一項);同一交付物的多個維度不算。單子項不問。
- 問完停下等回答;全部已清楚就跳過直接編——別對已經夠精確的請求硬問。

**契約 done**:沒有任何裸 `(assumed)`,且每條驗證指令都已查證可跑。

---

## 輸出格式(適用時)

### 1. 成功條件 (Success criteria)
可驗證的端狀態,且必須是 evaluator 在 transcript 裡找得到的證據:指令退出碼、輸出比對、可量化門檻(p95 < X ms)。使用者沒給的數字門檻先問(見 grilling);使用者明確要你自己定,才標 `(assumed,請確認)`。

### 2. 驗證指令 (Verification)
依總綱讀者 1 的限制編寫:

- ✅ `run \`npx playwright test login.spec.ts\` and paste output showing "X passed, 0 failed"`
- ❌ `tests pass` / `check the file is correct`(evaluator 判不了)

**先查證再輸出**:對每條驗證指令做唯讀 smoke check。不存在就標「⚠ 此驗證尚不存在,需先建立」並列為第一步;驗證目標本身就是任務交付物時(如「寫一個 script」)同樣處理,不構成矛盾。

**多子項規範 → 逐項差異報告**:驗證除指令輸出外,再加「貼出逐項實作報告:每個子項標 implemented / deviated,deviated 要說明差異」——堵住 loop 收斂了但建的不是你要的東西。grilling 選了 workflow 獨立驗證,報告改由驗證 workflow 產生(寫法見 #5)。

**搜尋型任務 → 收斂護欄**:任務要靠多輪「嘗試→驗證→再嘗試」才收斂(效能調校、flaky test 除錯、追 benchmark 數字)時,loop 的典型死法是同狀態下重提同一改法、連續失敗到回合上限(Bilevel Autoresearch, arXiv:2603.23420)。編譯時加兩條護欄(寫法見 #5):

- **trace 條款**(併入 until 段):`pasting every 5 turns a one-line search log: approaches tried → result → ruled out`——只記錄做了什麼與驗證結果,不要求解釋思考過程。
- **anti-fixation 條款**(併入 without 段):`without repeating an approach whose verification output has already failed twice`——重試必須換方向,不是換措辭。

非搜尋型任務(單次修 bug、加功能)兩條都不加——是雜訊。

### 3. 邊界 (Boundaries)
只列與本任務相關的面,不相關的整塊省略——不寫「N/A」:

- **不可改動**(Constraints):不得更動的行為/語義(public API、認證流程、輸出格式);其中**量尺路徑**(verification surface——驗證依賴的測試、bench script、CI 設定)列成明確路徑清單:量尺被動即作弊,這份清單也是收割時 diff 稽核的依據
- **可改路徑**(Write scope):允許寫 / 禁止碰的路徑
- **外部系統限制**(Action policy):read-only / draft-only / 不得 send·deploy·merge
- **最多幾回合**(預算):一律加回合上限;預設 `or stop after 12 turns`——Claude 5 世代單回合能完成過去整個 loop 的量,上限是停損不是額度,舊世代或較小模型實作時可放寬到 20——再依任務複雜度**與驗證成本**調整——loop 成本 ≈ 回合數 × 每回合驗證成本,驗證昂貴(整包 e2e、長 benchmark、完整 build)時下調上限,或內圈改跑便宜的 targeted check(如單一 spec 檔)、full suite 只當 final gate

### 4. 任務脈絡 (Context) — 選配,有才寫
一句話說明**為什麼做、任務壽命**(「這是實驗,一個月後很可能刪掉」勝過「保持簡單」)。只在 grilling 問出內容、或使用者已提供時出現;沒有就整節省略。

### 5. Ready-to-use `/goal` condition
合成一條 Claude Code `/goal` 可吃的**自然語言**字串(非結構化欄位)。骨架:

```
[context 一短句,若有 —] [做什麼] until [可量化端狀態,由執行 CMD 並貼出輸出證明]
without [constraints,多條用 AND 串] or stop after [N] turns
```

- 回合上限 N 依 #3 定案;condition 裡只出現定案的數字,不把調整說明抄進字串。
- 任務脈絡(#4)放 condition 開頭一短句(如 `context: this feature is a throwaway experiment —`),一句為限——evaluator 只 pattern-match until / without 部分,寫長是雜訊。
- 多子項規範:在 until 段最後一個驗證證據之後併入差異報告——自報版 `… and paste a per-item completion report (implemented / deviated, deviations explained)`;workflow 獨立驗證版 `… then run a verification workflow (one independent verifier per spec item, judging outcome against the spec) and paste its per-item report (implemented / deviated)`(後者由使用者親手貼進 `/goal`,正好構成 Workflow 工具需要的明確 opt-in)。
- 搜尋型任務:trace 條款接在 until 段末尾、anti-fixation 條款串進 without 段(#2)。

範例:

```
/goal "run npx playwright test login-flicker.spec.ts until it paste-shows 0 failures
       without modifying src/auth/ or any file outside src/components/LoginPage.tsx
       AND without removing any existing assertion
       or stop after 12 turns"
```

### 何時暫停 (Pause-if) — 獨立列出,**不要塞進上面的 condition**
Claude `/goal` 無原生 Pause-if 欄位;塞進 condition 字串 evaluator 會誤判為失敗而繼續 loop。改為獨立列出觸發情境,並建議用 Stop hook 實作(缺權限 / 需破壞性操作 / 需人工決策 / 同一驗證連續 3 回合輸出相同失敗——停滯訊號 / 文件衝突)。

loop 停滯、或撞回合上限仍未收斂時,別把原 condition 直接重掛——用 `/saygoal:retro` 讀 transcript 診斷停滯類別、結構性重寫契約。

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

- **`/codex:rescue`**(openai codex plugin):本 session 的 available skills 清單;不確定時備援 `jq -e '.plugins | has("codex@openai-codex")' ~/.claude/plugins/installed_plugins.json`
- **`codex-agent`**(codex-orchestrator):`command -v codex-agent`
- **`codex exec`**(裸 codex CLI,最通用、依賴最少):`command -v codex`

**一個都沒偵測到** → 不提委派:確認後可依契約直接實作(拿 Verification 當驗收清單;額度緊時建議),或複製 #5 貼入 `/goal` 讓 Claude Code loop 到收斂(需 v2.1.139+)。

**偵測到至少一個** → 讀專案偏好檔 `.claude/saygoal.local.json`(格式 `{"delegate": "self-goal" | "codex-rescue" | "codex-agent" | "codex-exec"}`),用 AskUserQuestion 問執行通道——**每次都問,不因偏好跳過**(每次委派都花額度,單次否決權留給使用者);偏好通道排第一標 `(Recommended)`,無偏好時「自己 `/goal` loop」排第一。選項只列偵測到的:

1. **自己 `/goal` loop**:輸出 #5 讓使用者貼(維持 `/dec` 不實作的邊界)
2. **委派 `/codex:rescue`**:契約 #1–#4 全文(不含 `/goal` 前綴)交 Codex 背景執行
3. **委派 `codex-agent`**:同上,適合多份契約平行 fan-out
4. **委派 `codex exec`**:最通用 fallback,只需 codex CLI、不需任何 plugin

使用者選定後:選擇與偏好檔不同(或首次)→ 寫回偏好檔(該檔未被 gitignore 時提醒一句,不要擅自改 `.gitignore`)。選 1 → 輸出 #5,結束。選 2 / 3 / 4 → **直接派發,不再確認**(剛才的選擇就是確認):

- 選 2:用 **Skill 工具**叫用 `codex:rescue`、args 為 `--background <契約全文>`(不是 Bash);收割 `/codex:status` + `/codex:result`。
- 選 3:Bash 跑 `codex-agent start "<契約全文>"`;收割 `codex-agent await-turn` + `output`。
- 選 4:Bash 跑 `codex exec -C <repo 根> --sandbox workspace-write --json "<契約全文>"`、帶 `run_in_background: true`(需網路,Claude 沙箱下要放行)。背景 task 提供進度查詢與完成通知;卡太久用 TaskStop 中止、收回自己做。收割讀 output 尾的最終 assistant 訊息(或派發時加 `-o <檔>` 單獨落最終訊息)。

**委派版契約的一個調整**:搜尋型任務的 trace 條款改為落檔版、併入契約文字——`after each attempt, append one line to .claude/saygoal.trace.log: <UTC time> | executor: <channel> | tried → result → ruled out`。委派行程沒有 transcript 連續性,收割與 `/saygoal:retro` 讀這個檔。

**派發前先編量尺 script**(實驗性):把契約編譯成一支 `.claude/saygoal.stop-check.sh` 落檔後再派發——整個 loop 依賴的那道閘門,不能交給實作模型自裁。script 規格:exit 0 唯若契約成立;真的執行驗證指令並比對關鍵字串,不信任何先前貼出的輸出;把派發當下的 `git rev-parse HEAD` 寫死為基準,量尺路徑 `git diff --name-only <基準> -- <路徑>` 非空即 fail;每條檢查印出證據與結論。Claude 與被委派模型共用這把尺,「完成」不再有兩種解讀。該檔未被 gitignore 時提醒一句。

派發後回報 job/task 資訊與收割方式。**收割三件套**:驗收只讀契約原文、`git diff`、驗證輸出——不讀實作過程,過程 token 不回灌。第一步執行 `.claude/saygoal.stop-check.sh` 並貼出輸出與 exit code,非 0 直接拒收(量尺 diff 稽核與驗證重跑都在 script 裡,不採信實作方自報);多子項另核差異報告。整套收割程序的可叫用形式是 `/saygoal:judge`——對委派成果直接叫它驗收即可。委派是**調度**,不違反「不要實作」:實作發生在被委派的模型,且以使用者當下的明確選擇為前提。

---

Request: $ARGUMENTS
