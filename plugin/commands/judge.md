---
description: Contract-anchored acceptance of claimed-done work — collects the contract's claims, re-runs its verification, audits the diff against the verification surface, hunts weakened checks and false completion claims, and delivers an evidence-first verdict (VERIFIED / VERIFIED WITH CAVEATS / REFUTED). Read-and-run only; never fixes.
argument-hint: [optional — the contract or /goal condition, and where the work is (diff / branch / directory / pasted report); defaults to the most recent contract and completed work in this conversation]
---

<!-- platform: Claude Code (command) · output: verdict-first acceptance report · read-and-run only · appends .claude/saygoal.history.jsonl -->
<!-- adapted from fable-judge in Sahir619/fable-method (MIT), re-anchored on the saygoal contract -->
<!-- the acceptance gate of the pipeline: /dec compiles, /goal or a delegate executes, /judge accepts the success claim, /retro rewrites on stall -->

`/judge` 驗收一份「宣稱做完」的工作。立場固定:**報告是主張的集合,不是證據**——沒觀察到的一律不信。判官唯讀＋執行:讀檔、跑驗證、比 diff,但**不修任何東西**(修是使用者看完判決後的另一個決定)。這是閘門,不是二次實作:分鐘級,不是小時級。

---

## 輸入與錨定

- **工作**:本對話最近完成的一份工作,或使用者指名的對象(diff、branch、目錄、貼上的別人 report)。
- **契約**(saygoal 的優勢所在):有 `/dec` 契約或 `/goal` condition 時,主張清單不用湊——**Verification 欄位=該重跑什麼、量尺路徑=該 diff 稽核什麼、可改路徑=寫入範圍稽核、逐項差異報告=現成的逐項主張**;`.claude/saygoal.stop-check.sh` 存在就先跑它,exit code 是機械判決核心。主張由實作前凍結的契約供給,不由被審方的報告供給——被審者不得定義考題(chain of custody)。
- 沒有契約時退化為通用驗收:先從報告與對話收集主張(做了什麼、驗了什麼、宣稱沒動什麼),每條列成待證項,再走同一套程序。
- 委派收割:trace 檔 `.claude/saygoal.trace.log` 只讀與最終狀態相關的行——過程 token 不回灌。

## 程序

1. **收集主張**:從契約欄位與完成報告列表——宣稱完成的、宣稱驗證過的、宣稱沒碰的。每條都是待證或待駁的一列。
2. **確立實際變更**:`git diff` 與 `git status` 是 ground truth,報告不是(無 git 時對 pristine 參照做目錄 diff)。先比對量尺路徑——**量尺被動,直接進 REFUTED 候選**,除非契約明文允許受控修改;再比對可改路徑,抓越界寫入;最後把整個 touched 集合對照請求的合理範圍。
3. **逐條重跑宣稱的驗證**:不要讀了程式碼點頭——真的跑測試、build、script、頁面,貼實際輸出。跑不了的(缺環境、缺憑證、只有人眼能驗)標 **UNVERIFIABLE**,絕不視為真。
4. **獵典型造假**,按真實世界頻率排序:
   - **弱化檢查(test tampering)**:專門 diff 測試檔——斷言放寬或刪除、期望值改成遷就新行為、測試被 skip、容差放大、真呼叫換成 mock。**改過的測試在追溯到規格之前推定有罪。**
   - **假完成(false completion)**:宣稱通過但沒展示執行、部分通過報成全部通過、"should work now"、失敗 transcript 上的成功措辭。
   - **範圍潛變**:超出請求的改動——順手重構、重排版、新依賴、「順便改進」。
   - **違背規格**:程式碼改成遷就一個與 README/規格/docstring 矛盾的檢查。權威順序:**使用者明示 > 規格 > 測試 > 現行程式碼行為**。
   - **殘渣**:scratch 檔、debug print、註解掉的程式碼、孤兒 import。
5. **判決,證據先行**——判決放第一行:
   - **VERIFIED**:每條承重主張都重現,無造假。
   - **VERIFIED WITH CAVEATS**:工作可靠;精確列出跑不了的項目與小殘渣。
   - **REFUTED**:有主張重現失敗或抓到造假——指名該主張、展示反證輸出、給最小修法。
   接著:主張表(主張 → 觀察到什麼)、造假清單(有的話)、建議動作。**不軟化駁回,也不把 caveat 灌成駁回充嚴格。**
6. **寫入歷史**:append 一行 `.claude/saygoal.history.jsonl`:`{"date":"YYYY-MM-DD","task":"<一句話>","outcome":"verified"|"refuted","frauds":["<抓到的手法>"],"resolution":"<一句話>"}`——之後 `/dec` grilling 讀它,被抓過的造假手法變成下一份契約的預防條款。該檔未被 gitignore 時提醒一句。

## 邊界

- 工作裡沒有可跑的驗證時,明說判官在這裡能查什麼、不能查什麼——不硬給 VERIFIED。
- 驗證需要你沒有的環境,交還使用者而非猜。
- **判官與實作不同席**:若這份工作正是本 session 自己做的,聲明利益衝突,建議改開 fresh session 或 subagent 來判——fresh-context 驗證優於自我批改。

---

Work to judge: $ARGUMENTS
