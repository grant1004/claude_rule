# claude_rule

Claude Code 的規則庫：在同一個專案同時處理多個問題的做法。這個 repo 主要是給 session 讀的；使用者只需要看「怎麼啟動」。

## 怎麼啟動（給使用者）

在專案目錄開 Claude Code，貼上下面這一行，把尖括號的部分換成自己的內容：

```
/goal 用 git clone 或 curl 取得 https://github.com/grant1004/claude_rule 的 README.md 原文（不要用摘要）並照做，處理下列問題，直到每個問題都是「已合併到 integration 且合併後全套測試通過」或「受阻並寫明原因」，而且最後一次回報列出了 WIP.md 的完整內容和最後一次全套測試的輸出。不可以刪除或放寬測試，不可以 push，不可以動 integration 以外的既有分支。最多 60 回合。問題：1. <問題一> 2. <問題二>。建置指令：<...>。全套測試指令：<...>。
```

- 想在每個階段自己把關，就把開頭的 `/goal ` 拿掉，改成一般訊息送出。
- 想先看過分組再開工，就在句尾加上「分組結果要先給我確認」，並且不要用 `/goal`。

## 你該做什麼（給 session）

使用者叫你讀這個 repo 時，依序做：

1. 取得 `parallel-lanes.md` 的原文並讀完，這次 session 照它做。網址：
   `https://raw.githubusercontent.com/grant1004/claude_rule/main/parallel-lanes.md`
2. 把它存成使用者層級規則，已存在就覆蓋。之後這台電腦的 session 和子代理都會自動載入。
   - Windows：`%USERPROFILE%\.claude\rules\parallel-lanes.md`
   - macOS、Linux：`~/.claude/rules/parallel-lanes.md`
3. 在專案裡把 `WIP.md` 和 `.claude/worktrees/` 加進 `.git/info/exclude`，已經有就略過。
4. 使用者沒有指定模式時用模式一，你就是協調者，從「分診與分組」開始。
5. 使用者沒有給建置或全套測試的指令時，先從專案的 CLAUDE.md 或 README 找；找不到再問。

## 收尾

全部問題都處理完之後才做，而且每一步都要使用者確認：

1. 併回正式分支：切到原本的分支，執行 `git merge --no-ff integration`。這是整個流程裡唯一會動到正式分支的地方。
2. 清理：先 `git worktree remove <worktree 路徑>`，再 `git branch -d <車道分支>`，最後 `git branch -d integration`。分支還被 worktree 使用時刪不掉，所以順序不能反。
3. 用 `git worktree list` 確認沒有殘留的 worktree。

## 檔案

| 檔案 | 用途 | 自動安裝 |
|---|---|---|
| `parallel-lanes.md` | 平行車道協定 | 要，照上面第 2 步 |
| `general-workflow.md` | 所有專案共用的工作通則：任務分級、分析、派工、驗證、規則增修 | 不要，使用者要求才裝。它每個 session 都會載入，比較佔 context |
| `CLAUDE.template.md` | 各專案 CLAUDE.md 的範本 | 不要，使用者要求才用 |
