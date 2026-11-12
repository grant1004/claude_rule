# claude_rule

讓 Claude Code 在每個專案、每個 session 都用同樣的方式工作的規則庫。

- 每個 session 載入同一份核心規則（`rules/core.md`）。
- 每種工作走同一份流程（`procedures/`），用到才讀。
- 每個專案的 CLAUDE.md 用同一個範本（`templates/`）。
- 每次完成任務都用同樣的格式回報，並列出規則版本。

目前版本見 `VERSION`。

## 安裝

每台電腦做一次。需要 git 和 Claude Code。

Windows（PowerShell）：

```powershell
git clone https://github.com/grant1004/claude_rule "$env:USERPROFILE\.claude\claude_rule"
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\rules" | Out-Null
Copy-Item "$env:USERPROFILE\.claude\claude_rule\rules\core.md" "$env:USERPROFILE\.claude\rules\claude_rule-core.md" -Force
```

macOS、Linux：

```bash
git clone https://github.com/grant1004/claude_rule ~/.claude/claude_rule
mkdir -p ~/.claude/rules
cp ~/.claude/claude_rule/rules/core.md ~/.claude/rules/claude_rule-core.md
```

裝完之後新開的 session 才會載入。

## 更新

Windows（PowerShell）：

```powershell
git -C "$env:USERPROFILE\.claude\claude_rule" pull
Copy-Item "$env:USERPROFILE\.claude\claude_rule\rules\core.md" "$env:USERPROFILE\.claude\rules\claude_rule-core.md" -Force
```

macOS、Linux：

```bash
git -C ~/.claude/claude_rule pull
cp ~/.claude/claude_rule/rules/core.md ~/.claude/rules/claude_rule-core.md
```

## 從舊版升級

2026-11-12 以前的版本會把 `parallel-lanes.md` 裝成常駐規則。照上面安裝之後，把舊檔刪掉：

- Windows：`Remove-Item "$env:USERPROFILE\.claude\rules\parallel-lanes.md"`
- macOS、Linux：`rm ~/.claude/rules/parallel-lanes.md`

## 確認有裝好

在任一個專案開新的 session：

- 打 `/context`，載入的檔案裡應該有 `claude_rule-core.md`。
- 問「規則版本是多少」，回答應該和 `VERSION` 一致。

## 怎麼用

每個專案第一次使用時先說「初始化專案」，讓它依範本產生這個專案的 CLAUDE.md。之後用固定的說法開工：

| 要做的事 | 固定說法 |
|---|---|
| 讓專案有標準的 CLAUDE.md | 初始化專案 |
| 開新專案 | 開新專案：<目標> |
| 修改或加功能 | 直接描述。想固定流程的深度，就在句首加「S：」「M：」或「L：」 |
| 多個問題一起處理 | 平行處理：1. <問題一> 2. <問題二> |
| 檢討並調整規則 | 回顧規則 |

每次完成任務的回報最後會列出規則版本和這次讀了哪些流程檔，可以用來確認它走的是同一套流程。

## 檔案

| 路徑 | 用途 | 什麼時候載入 |
|---|---|---|
| `rules/core.md` | 核心規則：分級、流程對照、驗證、待決事項、停損、回報格式 | 每個 session |
| `procedures/project-init.md` | 依範本產生專案的 CLAUDE.md | 說「初始化專案」時 |
| `procedures/new-project.md` | 開新專案前的啟動文件 | 說「開新專案」時 |
| `procedures/change.md` | 修改或加功能前要回答的六個問題 | M、L 級任務 |
| `procedures/parallel-lanes.md` | 多個問題平行處理 | 說「平行處理」時 |
| `procedures/dispatch.md` | 何時派子代理、派工單怎麼寫 | 準備派工時 |
| `procedures/testing.md` | 怎麼寫測試、怎麼讓檢查變快 | 寫或改測試時 |
| `procedures/rule-update.md` | 規則怎麼增修 | 說「回顧規則」時 |
| `templates/CLAUDE.template.md` | 專案 CLAUDE.md 的範本 | 初始化專案時 |

## 建議每台電腦都固定的設定

規則之外，這些設定也會影響行為。想要每次都一樣，就讓它們在每台電腦一致：

- 預設模型：在 `/config` 設定，每台電腦用同一個。
- effort：開工前用 `/effort` 確認是同一個等級。
- 權限模式：固定用同一種。
- worktree 的起點：在使用者層級的 `settings.json` 加上 `"worktree": { "baseRef": "head" }`，平行處理時子代理才會從本地的最新 commit 開始。

## 限制

- 規則是給模型的指示，不是強制機制。它提高一致性，但不保證每次行為相同。
- 真的不能有差異的步驟，例如收工前一定要跑全套測試，要用 hook 或 CI 來強制。
- 核心規則每個 session 都佔 context，所以上限是 80 行。要加東西先看 `procedures/rule-update.md`。
