# claude_rule

讓 Claude Code 在每個專案、每個 session 都用同樣的方式工作的規則庫。

- 每個 session 載入同一份核心規則（`rules/core.md`）。
- 主視窗只負責調度，修改交給同一組背景執行者（`agents/`），並由守門 hook 強制（`hooks/`）。
- 每種工作走同一份流程（`procedures/`），用到才讀。
- 每個專案的 CLAUDE.md 用同一個範本（`templates/`）。
- 每次回報都用同樣的格式，並列出規則版本。

目前版本見 `VERSION`。

## 主視窗怎麼運作

- 你說要改什麼，主視窗把它記進 `WIP.md`，判斷它和進行中的任務有沒有衝突，派給背景執行者，然後馬上把對話還給你。改程式碼、跑建置和測試都在背景進行，輸出不會洗掉主視窗的內容。
- 主視窗自己改不了專案檔案：守門 hook 會擋下它的修改，並告訴它改成派工。它能寫的只有 `WIP.md`、專案的 CLAUDE.md 和 `docs/` 底下的 Markdown 文件。
- 和進行中的任務沒有衝突的，會同時做：第二個以後在獨立的 git worktree 裡做，完成後由主視窗合併。有衝突的排隊，前一個落地後自動接著做。
- 執行者做完還叫得回來。排隊的後續任務會交給剛做完前一個任務的同一個執行者；閒置的隔離執行者會留著它的 worktree 給下一個任務用，省掉重新建置。同一個執行者最多連做 3 個任務。
- 執行者驗證通過後會自動 commit 到你目前的分支，不 push。不想讓它自動 commit 的專案，在專案 CLAUDE.md 的 Git 段寫明；那個專案就一次只做一個任務。
- 要你回答的事放在回覆的最後。你回答之前，那個任務停著等你，其他任務照常進行；還沒回答的問題每次回覆都會重列。
- 執行者需要權限時，詢問會出現在主視窗。

## 安裝

每台電腦做一次。需要 git 和 Claude Code；Windows 上守門 hook 需要 Git Bash（Git for Windows 內附）。

Windows（PowerShell）：

```powershell
git clone https://github.com/grant1004/claude_rule "$env:USERPROFILE\.claude\claude_rule"
```

macOS、Linux：

```bash
git clone https://github.com/grant1004/claude_rule ~/.claude/claude_rule
```

接著做下面的「套用」和「設定檔」。

## 套用

第一次安裝和之後每次更新都跑同一段。跑完要新開 session 才會生效。

Windows（PowerShell）：

```powershell
git -C "$env:USERPROFILE\.claude\claude_rule" pull
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\rules" | Out-Null
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\agents" | Out-Null
Copy-Item "$env:USERPROFILE\.claude\claude_rule\rules\core.md" "$env:USERPROFILE\.claude\rules\claude_rule-core.md" -Force
Copy-Item "$env:USERPROFILE\.claude\claude_rule\agents\*.md" "$env:USERPROFILE\.claude\agents" -Force
```

macOS、Linux：

```bash
git -C ~/.claude/claude_rule pull
mkdir -p ~/.claude/rules ~/.claude/agents
cp ~/.claude/claude_rule/rules/core.md ~/.claude/rules/claude_rule-core.md
cp ~/.claude/claude_rule/agents/*.md ~/.claude/agents/
```

## 設定檔

每台電腦做一次。在使用者層級的 `settings.json`（`~/.claude/settings.json`，Windows 是 `%USERPROFILE%\.claude\settings.json`；沒有就新建）加入下面兩段。檔案裡已經有 `permissions` 或 `hooks`，就把內容併進原本的區塊，不要整個蓋掉。

```json
{
  "permissions": {
    "allow": ["Read(~/.claude/claude_rule/**)"]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|NotebookEdit",
        "hooks": [
          {
            "type": "command",
            "command": "sh \"$HOME/.claude/claude_rule/hooks/cr-guard.sh\" || true"
          }
        ]
      }
    ]
  }
}
```

### `permissions`：讓流程檔不用問就讀得到

流程檔放在專案資料夾外面（`~/.claude/claude_rule/`），而 Claude Code 讀專案外的檔案不一定直接放行：

- Manual 模式：只有工作目錄裡的讀取不用同意，專案外的會先問你。這條 allow 規則處理的就是這個詢問。
- auto 模式：第一次讀專案外的檔案時會問一次，被問到就選允許。選了「No, and block reads outside the working directories from now on」，這台電腦之後每個 session、每種權限模式都讀不到流程檔。
- 這台電腦如果已經開了 `permissions.blockReadsOutsideWorkingDirectories`，依 Claude Code 的文件，要把 `claude_rule` 資料夾的完整路徑加進使用者層級的 `permissions.additionalDirectories`，或把那個設定從設定檔拿掉，流程檔才讀得到。

### `hooks`：守門，強制每次都派工

`hooks/cr-guard.sh` 在每次 Edit、Write、NotebookEdit 之前執行：

- 呼叫來自子代理（執行者）：放行。
- 呼叫來自主視窗，而且目標是專案檔案：擋下，並告訴它改成派工。
- 主視窗寫 `WIP.md`、CLAUDE.md、`docs/` 底下的 Markdown、Claude Code 自己的檔案（`.claude/` 底下，例如計畫檔和記憶），以及 plan 模式：放行。

要注意的事：

- 腳本壞掉或找不到時，它不會擋任何東西，也不會報錯。這台電腦沒有 Git Bash 時同樣擋不了，還可能每次修改都顯示一則 hook 錯誤。所以裝完一定要照「確認有裝好」測一次。
- 它只管這三個編輯工具。主視窗用 Bash 或 PowerShell 指令改檔、在前景跑建置或測試，它擋不到；這兩件事靠核心規則。
- 需要自己改檔的 session，啟動前先設環境變數 `CR_GUARD=off`（PowerShell：`$env:CR_GUARD = "off"`，然後在同一個視窗啟動 `claude`）。例如平行車道的模式二，或你另外用來當執行者的 session。

## 從舊版升級

照「套用」和「設定檔」做一次，再處理下面的事：

- 0.3.0 之前的版本會把 `parallel-lanes.md` 裝成常駐規則；當時如果另外裝了通則，`general-workflow.md` 也在同一個資料夾。留著會和新規則同時載入，把舊檔刪掉（檔案不存在也不會報錯）：
  - Windows：`Remove-Item "$env:USERPROFILE\.claude\rules\parallel-lanes.md", "$env:USERPROFILE\.claude\rules\general-workflow.md" -ErrorAction SilentlyContinue`
  - macOS、Linux：`rm -f ~/.claude/rules/parallel-lanes.md ~/.claude/rules/general-workflow.md`
  - 其他地方放過這兩個檔案的話（例如某個專案的 `.claude/rules/`），也要一併刪掉。
- 0.3.x 的平行處理會建立 `integration` 分支。0.4.0 起任務直接落在你目前的分支，不再用它；專案裡如果留有這個分支，確認內容已經併回之後可以刪掉。
- 0.4.0 的「直接改：」在 0.5.0 拿掉了，所有修改都派工。

進行到一半的 session 不會換成新規則。新開一個 session，說「接續」，它會從 `WIP.md` 接手。

## 確認有裝好

在任一個專案開新的 session：

- 打 `/context`，載入的檔案裡應該有 `claude_rule-core.md`。
- 問「規則版本是多少」，回答應該和 `VERSION` 一致。
- 輸入 `@cr-`，選單裡應該出現 `cr-worker` 和 `cr-worker-isolated`。
- 說「讀 change.md 流程檔，告訴我它的標題」，回答應該是「修改既有專案或新增功能」，而且過程中沒有跳出權限詢問。有跳出來，就回頭檢查 `permissions` 那一段。
- 打 `/hooks`，清單裡應該有來自使用者設定的 PreToolUse hook。然後說「測試守門 hook：你自己用 Edit 工具在 README.md 最後加一個空行，被擋下來就把訊息原文貼給我，不要改用別的方法」。應該看到開頭是 `claude_rule guard` 的訊息。修改成功了，就代表守門 hook 沒有生效：把那一行還原，回頭檢查 `hooks` 那一段和 Git Bash。

## 怎麼用

每個專案第一次使用時先說「初始化專案」，讓它依範本產生這個專案的 CLAUDE.md。之後用固定的說法：

| 要做的事 | 固定說法 |
|---|---|
| 讓專案有標準的 CLAUDE.md | 初始化專案 |
| 開新專案 | 開新專案：<目標> |
| 修改或加功能 | 直接描述。想固定流程的深度，就在句首加「S：」「M：」或「L：」 |
| 多個問題一起處理 | 平行處理：1. <問題一> 2. <問題二> |
| 新 session 接手上一個 session 的任務 | 接續 |
| 結束一批任務，清理執行者留下的 worktree | 收尾 |
| 檢討並調整規則 | 回顧規則 |

每次回報的最後會列出規則版本和這次讀了哪些流程檔，可以用來確認它走的是同一套流程。

## 主視窗被佔住的時候

守門 hook 擋的是改檔，主視窗還是可能在前景做別的事。這幾個按鍵是 Claude Code 內建的：

- `/btw <問題>`：側邊提問，不打斷正在進行的工作。它只能用對話裡已有的內容回答，不能讀檔或跑指令。
- 打完訊息按 `Ctrl+Enter`（終端機不支援就按 `Ctrl+X Ctrl+S`；需要 Claude Code v2.1.275 以上）：正在跑的指令或子代理會移到背景繼續跑，它馬上讀你的訊息。
- `Ctrl+B`：把正在跑的指令或子代理移到背景。
- `Ctrl+O`：開對話紀錄，找被洗掉的回覆。

## 檔案

| 路徑 | 用途 | 什麼時候載入 |
|---|---|---|
| `rules/core.md` | 核心規則：主對話只調度、分級、流程對照、驗證、待決事項、停損、回報格式 | 每個 session |
| `agents/cr-worker.md` | 就地執行者：在工作目錄實作、驗證、commit | 主視窗派工時 |
| `agents/cr-worker-isolated.md` | 隔離執行者：在自己的 worktree 實作，由主視窗合併 | 主視窗派工、而工作目錄有人在用時 |
| `hooks/cr-guard.sh` | 守門 hook：擋下主視窗對專案檔案的修改 | 每次 Edit、Write、NotebookEdit 之前 |
| `procedures/dispatch.md` | 派工、重複使用執行者、驗收、落地、收尾，以及 `WIP.md` 的格式 | 第一次派工時 |
| `procedures/parallel-lanes.md` | 多個問題一次分診、分組、平行派出 | 說「平行處理」時 |
| `procedures/change.md` | 修改或加功能前要回答的六個問題 | M、L 級任務 |
| `procedures/project-init.md` | 依範本產生專案的 CLAUDE.md | 說「初始化專案」時 |
| `procedures/new-project.md` | 開新專案前的啟動文件 | 說「開新專案」時 |
| `procedures/testing.md` | 怎麼寫測試、怎麼讓檢查變快 | 寫或改測試時 |
| `procedures/rule-update.md` | 規則怎麼增修 | 說「回顧規則」時 |
| `templates/CLAUDE.template.md` | 專案 CLAUDE.md 的範本 | 初始化專案時 |

## 建議每台電腦都固定的設定

規則之外，這些設定也會影響行為。想要每次都一樣，就讓它們在每台電腦一致：

- 預設模型：在 `/config` 設定，每台電腦用同一個。
- effort：開工前用 `/effort` 確認是同一個等級。
- worktree 的起點：在使用者層級的 `settings.json` 加上 `"worktree": { "baseRef": "head" }`。沒設也能運作（隔離執行者會自己從落地分支開分支），但會多留下一個要手動清的空分支。
- 權限模式：固定用同一種。可以在使用者層級的 `settings.json` 用 `permissions.defaultMode` 指定新 session 的起始模式。主視窗是 Manual 模式時，執行者的檔案修改不會逐一詢問（執行者定義裡設了 `permissionMode: acceptEdits`），建置、測試、commit 這類指令仍然會問；不想被問，就把這些指令加進專案的 allow 規則，或用 auto 模式。
- 不要開啟 agent teams（`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`）。開啟時，被取了名字的執行者會變成隊友，在主視窗的工作目錄裡跑，不會被隔離。隔離執行者發現自己沒被隔離時會停下來回報。

## 限制

- 核心規則是給模型的指示，不是強制機制。強制的只有守門 hook 管的那一件事：主視窗不能用編輯工具改專案檔案。
- 其他不能有差異的步驟，例如收工前一定要跑全套測試，要另外用 hook 或 CI 來強制。
- 同時做多個任務需要 git，而且專案允許自動 commit。隔離執行者的 worktree 是全新的 checkout：沒有建置快取，被 gitignore 的本機設定和外部函式庫也不在裡面。建置不起來時它會回報，主視窗會改成排隊就地做。要讓 worktree 帶上被 gitignore 的檔案，在專案根目錄加 `.worktreeinclude`。
- 兩個任務同時跑測試會共用同一台機器。測試會搶同一個連接埠、模擬器或固定路徑的專案，在專案 CLAUDE.md 的 Git 段寫明不能平行。
- 「同一個執行者最多連做 3 個任務」是估計值，沒有實測依據。執行者每次被叫回來都要重讀自己全部的歷史，做得越多越貴；覺得太早或太晚換人，就改 `procedures/dispatch.md` 裡的數字。
- 核心規則每個 session 都佔 context，所以上限是 100 行。要加東西先看 `procedures/rule-update.md`。
