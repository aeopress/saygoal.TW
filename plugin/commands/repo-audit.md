---
description: Principal-level repo audit → evidence-verified findings → agent-executable task plan, each task ending with a ready-to-paste /goal condition
argument-hint: [optional focus — a subdirectory, dimension, or concern]
---

<!-- platform: Claude Code (command) · output: AUDIT.md at repo root · read-only -->
<!-- adapted from https://gist.github.com/OmerFarukOruc/753f95b1ac278b683be83ed26b3bcc1f -->
<!-- saygoal adaptation: per-task /goal conditions (follow /dec evaluator rules) + token-budget scaling -->

# Repo Audit & Improvement Plan

## 背景 — 這份 audit 為何存在
維護者沒時間手工盤點技術債。你的 audit 會成為未來 Claude Code session 的工作佇列:每個任務都會交給一個沒有其他上下文的全新 agent。據此行事——要真相不要安慰,報喜不報憂的報告毫無價值。

本次 audit 焦點(若有): $ARGUMENTS

## 鐵則
- 每個 finding 引用你本次 session 真正讀過的 file:line。無法驗證的主張標註 unverified——絕不用猜的。寫最終報告前,逐一核對每個主張是否有本 session 的工具輸出佐證。
- 只分析。不修改程式碼、設定或依賴。你唯一建立的檔案是報告本身。
- 不要只讀「健康聲明」——實際觀察。在可行範圍內執行 repo 自己的唯讀指令(install、lint、type-check、測試、依賴稽核),並如實回報:測試失敗就明說失敗並附上輸出。
- 按專案成熟度校準——不要拿企業級標準要求 prototype。repo 很大時,深入做 80% 工作量的核心 20%,並說明略過了什麼。
- auditor 階段**全報**、不自我抑制:「只報高嚴重度」「保守一點」這類指令會讓模型照字面少報,壓的是 recall;數量與品質的閘門在下游的機械查證與 refuter。事實與判斷分開。某維度健康就用一句話帶過。真正的優點也要列——那是該保護的東西。

## 工作方式
- 若你在 plan mode 被啟動:所有決策都已寫在這裡,你的計畫只有一行(「依此規格執行 audit」),立即送審。
- 並行展開 subagents:先用 Explore agents 做探索,再為每個 audit 維度開一個 auditor,單一批次並行發出,且每個都拿到 repo map 不必重推。它們執行時你持續綜合。
- repo 工具(pnpm、yarn、linter)不在 PATH 時,先試 corepack 或版本管理 shims(mise、asdf、nvm)再下結論。
- 預設用一般 subagent(Agent tool):你能在波次之間持續綜合、引導 refuter、複核引用。只有邀請語含「use a workflow」或「ultracode」才改用 Workflow tool 編排 fan-out——把這些詞當編排 opt-in,不是 audit 焦點。若邀請語含 token 預算(如「+500k」),據此縮放 auditor 數量與深度。
- 挖 git 歷史,不只看快照:高 churn × 高複雜度檔案、bug-fix 密集模組、被棄置的目錄、TODO/FIXME 的年齡。
- 機械白名單先行:每個 finding 引用的 file:line 先用程式碼層查證(檔案存在、行號不超出檔案行數),查證不過直接剔除並記 warning——不修正、不重問。
- 對抗式驗證:任何 Critical 或 High finding 進報告前,必須由一個 fresh-context subagent 對著實際程式碼嘗試反駁。撐不過的就刪除或降級——這裡才是數量的閘門。
- 一路做到底不中途請示——這是唯讀且安全的。資訊足以行動時,就行動。

## Phase 1 — Discovery(先讀懂再評判)
盤點:目的與目標使用者、技術棧與 runtime、進入點、核心模組、主要資料/控制流、build/CI/環境設定、既有慣例(讓建議融入文化而非對抗它)、成熟度。產出精簡 Repo Map,包含任何令你意外的東西。

## Phase 2 — Audit
維度:架構與分層;程式碼品質(重複、dead code、複雜度熱點、被吞掉的錯誤、型別安全漏洞);安全(secrets、injection、缺驗證、auth 弱點、有漏洞的依賴);測試(核心邏輯的缺口、什麼都沒斷言的測試);效能(N+1 查詢、async 路徑上的阻塞呼叫、無上限增長);依賴(過時、無人維護、過重,lockfile 衛生);DevEx 與 ops(build 摩擦、CI 缺口、可觀測性、部署故事);文件 vs 現實。

每個 finding:what、where(file:line)、為何重要、嚴重度(Critical/High/Medium/Low)、信心、事實或判斷。

## Phase 3 — 改善策略
解釋多數 findings 的 3–5 個主題;每主題的目標狀態與背後原則;明確「不修什麼」與原因(投入 vs 回報);「done」定義為可量測訊號(如「CI 在 lint error 時 fail」、「核心路徑 coverage ≥ 80%」)。

## Phase 4 — 任務計畫
每個任務要讓全新 Claude Code session 只憑簡報就能執行:標題、一段背景、影響檔案、盡可能寫成可執行檢查的驗收條件(一條會 pass 或 fail 的指令)、工作量(S <2h、M 半天、L 1–2 天、XL 需再拆)、風險、依賴。

**每個任務最後附一條 ready-to-paste 的 `/goal` condition**,遵守 `/dec` 的 evaluator 規則:驗證寫成「執行 CMD 並貼出輸出證明」的形式、指定可 pattern-match 的字串或數字、禁用 ensure/verify/make sure 這類動詞、結尾加 `or stop after 20 turns`。

里程碑排序:
- M0 — 安全網:核心路徑測試、CI gates
- M1 — 關鍵修復:安全與正確性
- M2 — 高槓桿:讓所有後續工作更容易的改動
- M3 — 品質與打磨

Quick wins(高影響、S 工作量)獨立標出。前 3 個任務附實作草圖。

## 交付物
在 repo root 寫一個檔案 `AUDIT.md`。開頭:受稽核的 commit SHA、日期、一段方法說明並以 refuter 統計收尾(被駁回 / 降級 / 存活的 findings 數)。接著:Executive Summary(健康等級 A–F、前 3 風險、前 3 機會)→ Repo Map → Audit Report(最嚴重的在前)→ 改善策略 → 任務計畫 → 開放問題(每條指名需要維護者做的決定)。

寫給沒看過程的讀者:結論先行、完整句子、術語講明、不用工作中的簡寫。不灌水——靠取捨精簡,不靠壓縮文字。
