# Life Tracer MVP 项目设计文档

> 用途：这份文档用于交给 Codex，让它在 Debian 2GB VPS 环境中，从零开始实现一个轻量、可迁移、可导入外部工作会话、可手动调用 LLM 整理的个人 Life Tracer 系统。  
> 核心原则：先做最小可用系统，不做复杂笔记软件，不依赖 Docker，不依赖现成笔记软件，不把 LLM 写成系统运行的必要条件。

---

## 0. 项目背景

用户需要一个私人 Life Tracer 系统，用来记录：

1. 今天做了什么。
2. 当下有什么想法。
3. 哪些想法属于人生感悟、长期判断、方法论。
4. Codex / Claude Code 等工具中的工作会话。
5. 导入后的聊天记录、命令记录、项目修改记录。
6. 以后可以让 LLM 手动整理、分类、总结、提取待办事项。

这不是普通日记，也不是 Notion / Obsidian / Evernote 的替代品。  
它更接近一个“个人行为、想法、工作会话、判断过程”的时间戳数据库。

用户的现实限制：

- VPS：Debian，2GB 内存。
- 不想用 Docker。
- 不想买域名。
- 需要免费方案。
- 需要手机浏览器能快速打开。
- 需要数据容易迁移和备份。
- 需要支持中文为主、夹杂英文的记录。
- 需要支持 OpenRouter 或 MiniMax 等 LLM API，但 LLM 整理必须手动触发，避免 API 费用失控。
- 需要能导入 Codex / Claude Code 的聊天记录，格式可能是 JSONL、JSON、Markdown 或复制粘贴文本。

---

## 1. 项目目标

### 1.1 第一版 MVP 的目标

第一版只做最重要的功能：

1. 手机网页快速写入一条记录。
2. SQLite 保存原始记录。
3. 支持导入 Codex JSONL。
4. 预留导入 Markdown / JSON / 粘贴文本的接口。
5. 导入时保留原始文件，不直接覆盖。
6. Codex importer 只提取最重要信息，不展开每个工具调用细节。
7. 手动点击按钮调用 LLM 整理。
8. LLM 能区分：
   - 人生感悟 LifeInsight
   - 技术工作 Coding
   - 系统设计 SystemDesign
   - 教学 Teaching
   - 研究想法 ResearchIdea
   - 待办 ActionItem
   - 普通记录 Log
9. 今日记录页面。
10. 搜索页面。
11. JSONL 导出。
12. Markdown 导出。
13. 简单密码保护。
14. 支持 Cloudflare Quick Tunnel 这种无域名临时 HTTPS 访问方式。
15. 整个 `data/` 文件夹可复制迁移。

### 1.2 第一版不做的内容

不要做：

- React 前端。
- 手机原生 App。
- 图表 dashboard。
- 多用户系统。
- 富文本编辑器。
- 图片上传。
- 语音输入。
- 自动定时 LLM 整理。
- 复杂 agent。
- 知识图谱。
- 全量 diff 可视化。
- 完整还原 Codex 每个 tool call 的细节页面。
- 复杂权限系统。
- Docker 部署。

第一版必须像一张干净的白色记录卡片：打开、输入、保存、导入、整理、导出。

---

## 2. 技术方案

### 2.1 推荐技术栈

后端：

```text
FastAPI
SQLite
Jinja2 templates
Python standard library
```

前端：

```text
普通 HTML
普通 CSS
少量 JavaScript
<textarea>
<button>
<form>
```

运行方式：

```text
Python venv
systemd
uvicorn
```

公网访问：

```text
开发/初期：Cloudflare Quick Tunnel
长期可选：Tailscale Funnel 或以后购买便宜域名 + Cloudflare Tunnel
```

LLM：

```text
OpenRouter provider
MiniMax provider
未来可加 local provider / mock provider
```

### 2.2 为什么不用 Docker

用户 VPS 只有 2GB 内存。Docker 不是绝对不能跑，但它会增加：

- 镜像体积。
- 内存占用。
- 日志和数据卷管理复杂度。
- 故障排查成本。
- 部署步骤复杂度。

这个项目的第一版只需要 Python + SQLite。  
使用 venv + systemd 更轻。

### 2.3 为什么不用 PostgreSQL

第一版只给一个人使用，数据量主要是文本记录。SQLite 足够。  
SQLite 文件可直接复制备份，这是 Life Tracer 的迁移优势。

### 2.4 为什么不用复杂前端框架

第一版的核心是数据结构和导入整理流程，不是页面美观。  
前端框架会增加构建、依赖、Node 环境和部署复杂度。  
手机端只需要一个大输入框、几个按钮、简单列表。

---

## 3. 项目目录结构

建议目录：

```text
life-tracer/
  app/
    __init__.py
    main.py
    config.py
    db.py
    models.py

    auth.py
    export.py

    importers/
      __init__.py
      base.py
      codex_jsonl.py
      markdown_importer.py
      json_importer.py
      pasted_text.py

    llm/
      __init__.py
      base.py
      openrouter.py
      minimax.py
      prompts.py
      organizer.py

    templates/
      layout.html
      index.html
      today.html
      import.html
      import_detail.html
      organize.html
      search.html
      export.html
      login.html

    static/
      style.css
      app.js

  data/
    tracer.sqlite
    imports/
      raw/
      processed/
      failed/
    exports/
      jsonl/
      markdown/
    backups/

  scripts/
    init_db.py
    backup.sh
    export_all.py
    run_dev.sh

  .env.example
  requirements.txt
  README.md
```

第一版不需要把结构拆得太复杂，但建议一开始就留下 `importers/` 和 `llm/` 两个模块，因为这是项目的核心扩展点。

---

## 4. 数据保存原则

### 4.1 原始数据永远保留

任何手动输入、JSONL 导入、Markdown 导入，都必须先保存原始内容。

不要让 LLM 直接覆盖原文。  
不要导入后只保存摘要。  
不要把原始 Codex JSONL 解析完就删除。

正确做法：

```text
raw source file
  ↓
raw_import 表
  ↓
parsed session / turn / record
  ↓
LLM output 表
```

### 4.2 LLM 输出单独保存

LLM 整理结果可能不准确，以后可能换模型、换 prompt、重跑整理。  
所以整理结果必须单独存，不覆盖原始内容。

### 4.3 SQLite + JSONL + Markdown 三层保存

运行时：

```text
SQLite
```

程序迁移和二次处理：

```text
JSONL
```

人类阅读和长期归档：

```text
Markdown
```

---

## 5. 数据库设计

### 5.1 raw_imports

保存所有导入文件或粘贴文本的原始内容。

```sql
CREATE TABLE IF NOT EXISTS raw_imports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT NOT NULL,
    source_name TEXT,
    original_filename TEXT,
    stored_path TEXT,
    raw_text TEXT,
    imported_at TEXT NOT NULL,
    parse_status TEXT NOT NULL DEFAULT 'pending',
    parse_error TEXT
);
```

字段说明：

- `source_type`：`codex_jsonl` / `claude_code` / `markdown` / `json` / `pasted_text`
- `source_name`：用户给的名称，或系统自动推断。
- `original_filename`：上传文件名。
- `stored_path`：保存在 `data/imports/raw/` 下的路径。
- `raw_text`：如果是粘贴文本，可以直接存这里；如果是大文件，可以只存路径。
- `parse_status`：`pending` / `parsed` / `failed`
- `parse_error`：解析失败原因。

### 5.2 sessions

保存一次外部工作会话，比如一次 Codex 会话。

```sql
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_import_id INTEGER,
    source_type TEXT NOT NULL,
    source_session_id TEXT,
    project_name TEXT,
    project_path TEXT,
    started_at TEXT,
    ended_at TEXT,
    title TEXT,
    metadata_json TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(raw_import_id) REFERENCES raw_imports(id)
);
```

字段说明：

- `source_type`：例如 `codex`
- `source_session_id`：Codex JSONL 里的 session id。
- `project_name`：从 cwd 推断，如 `calculus_area_viewer`
- `project_path`：例如 `/root/workspace/job/calculus_area_viewer`
- `metadata_json`：保存 cli_version、model_provider、originator 等额外信息。

### 5.3 session_turns

保存一次会话中的关键轮次。  
这是 Codex importer 最重要的输出表。

```sql
CREATE TABLE IF NOT EXISTS session_turns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    source_turn_id TEXT,
    turn_index INTEGER NOT NULL,
    user_request TEXT,
    final_summary TEXT,
    started_at TEXT,
    completed_at TEXT,
    duration_ms INTEGER,
    time_to_first_token_ms INTEGER,
    raw_refs_json TEXT,
    llm_status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES sessions(id)
);
```

字段说明：

- `user_request`：用户给 Codex 的任务。
- `final_summary`：Codex 最终的 `task_complete.last_agent_message`。
- `raw_refs_json`：保存相关原始 JSONL 行号，方便以后追踪。
- `llm_status`：`pending` / `organized` / `failed`

### 5.4 tool_events

保存重要工具事件，但第一版不要展示全部细节。

```sql
CREATE TABLE IF NOT EXISTS tool_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    session_turn_id INTEGER,
    source_turn_id TEXT,
    event_type TEXT NOT NULL,
    tool_name TEXT,
    success INTEGER,
    changed_files_json TEXT,
    command_text TEXT,
    output_excerpt TEXT,
    raw_line_start INTEGER,
    raw_line_end INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES sessions(id),
    FOREIGN KEY(session_turn_id) REFERENCES session_turns(id)
);
```

字段说明：

- `event_type`：`patch_apply_end` / `exec_command` / `function_call_output` / `agent_message` / `error`
- `changed_files_json`：从 patch 的 `changes` 字段抽取文件名。
- `command_text`：如果是命令调用，保存命令。
- `output_excerpt`：保存短输出，不保存大段完整日志。
- 完整工具事件仍然可以通过 raw import 找回。

### 5.5 entries

保存用户手动写入的普通 Life Tracer 记录。

```sql
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    date TEXT NOT NULL,
    record_type TEXT NOT NULL DEFAULT 'Log',
    raw_content TEXT NOT NULL,
    normalized_content TEXT,
    tags TEXT,
    project TEXT,
    source_type TEXT NOT NULL DEFAULT 'manual',
    source_ref_id INTEGER,
    llm_status TEXT NOT NULL DEFAULT 'pending',
    is_deleted INTEGER NOT NULL DEFAULT 0
);
```

`record_type` 第一版允许：

```text
Log
Done
Thought
Question
Decision
Next
LifeInsight
```

### 5.6 llm_outputs

所有 LLM 结果统一放这里。  
这样 entries、session_turns 都可以用同一张表保存整理结果。

```sql
CREATE TABLE IF NOT EXISTS llm_outputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_type TEXT NOT NULL,
    target_id INTEGER NOT NULL,
    task_type TEXT NOT NULL,
    provider TEXT,
    model TEXT,
    prompt_version TEXT,
    output_json TEXT NOT NULL,
    summary TEXT,
    category TEXT,
    secondary_category TEXT,
    is_life_insight INTEGER,
    action_items_json TEXT,
    tags_json TEXT,
    created_at TEXT NOT NULL,
    error TEXT
);
```

字段说明：

- `target_type`：`entry` / `session_turn` / `session` / `daily`
- `target_id`：对应表 ID。
- `task_type`：`organize_record` / `organize_turn` / `daily_review`
- `output_json`：LLM 原始 JSON 输出。
- `summary`：常用摘要字段冗余存储，方便页面展示。
- `category`：主分类。
- `secondary_category`：细分类。
- `is_life_insight`：是否为人生感悟。

### 5.7 daily_reviews

保存每日总结。

```sql
CREATE TABLE IF NOT EXISTS daily_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,
    summary TEXT,
    done_summary TEXT,
    thought_summary TEXT,
    life_insights_json TEXT,
    coding_summary TEXT,
    teaching_summary TEXT,
    research_summary TEXT,
    action_items_json TEXT,
    open_questions_json TEXT,
    model TEXT,
    provider TEXT,
    created_at TEXT NOT NULL
);
```

---

## 6. 页面设计

### 6.1 `/` 快速记录页

功能：

- 大输入框。
- 类型选择按钮。
- 标签输入。
- 项目输入，可选。
- 保存按钮。
- 显示今天最近 10 条记录。
- 每条记录旁边有“整理”按钮。

页面元素：

```text
[textarea: raw_content]

Type:
[Log] [Done] [Thought] [Question] [Decision] [Next] [LifeInsight]

Tags:
[input]

Project:
[input]

[Save]
```

### 6.2 `/today`

功能：

- 按时间展示今天所有 entries。
- 展示今天导入的 sessions / turns。
- 每条记录显示：
  - 时间
  - 类型
  - 原文
  - LLM 分类和摘要，如果已有
  - “整理这条”按钮
- 页面顶部有：
  - “总结今天”按钮
  - “导出今天 Markdown”按钮

### 6.3 `/import`

功能：

- 上传 JSONL / JSON / Markdown。
- 粘贴文本。
- 选择 source_type：
  - `codex_jsonl`
  - `claude_code`
  - `markdown`
  - `json`
  - `pasted_text`
- 提交后进入 import_detail 页面。

### 6.4 `/import/{id}`

功能：

- 显示 raw import 信息。
- 显示 parse_status。
- 如果是 Codex JSONL，显示解析出的 session。
- 显示 session_turns 列表。
- 每个 turn 有“整理”按钮。
- 有“整理全部关键 turn”按钮，但仍然手动触发。

### 6.5 `/organize`

功能：

- 列出待整理的 entries 和 session_turns。
- 支持手动选择：
  - 整理单条记录
  - 整理某个 turn
  - 整理今天
  - 整理某个导入 session

### 6.6 `/search`

功能：

- 关键词搜索。
- 搜索范围：
  - entries.raw_content
  - entries.normalized_content
  - session_turns.user_request
  - session_turns.final_summary
  - llm_outputs.summary
- 筛选：
  - category
  - record_type
  - source_type
  - project
  - date range

### 6.7 `/export`

功能：

- 导出全部 JSONL。
- 导出全部 Markdown。
- 导出某一天 Markdown。
- 导出某个 session Markdown。
- 手动创建 SQLite 备份。

---

## 7. Importer 总体设计

Importer 是这个项目最重要的模块之一。

它不是为了完整还原所有聊天细节，而是为了把外部工作会话压缩成可追踪、可复盘、可整理的 Life Tracer 记录。

### 7.1 Importer 的总原则

1. 原始数据必须完整保存。
2. 解析结果只提取最重要内容。
3. 不把每个工具调用都变成主记录。
4. 不把大量日志塞进 daily record。
5. 不丢失和任务结果直接相关的关键信息。
6. LLM 整理前，先做结构化提取。
7. LLM 整理后，结果单独保存。
8. 解析失败不能影响原始文件保存。
9. importer 必须可重跑。
10. importer 输出要适合 Markdown 导出和 LLM 整理。

### 7.2 Importer 基类

建议定义：

```python
class BaseImporter:
    source_type: str

    def can_handle(self, filename: str, content: str) -> bool:
        ...

    def save_raw(self, file_or_text) -> RawImport:
        ...

    def parse(self, raw_import: RawImport) -> ImportResult:
        ...
```

`ImportResult` 可以包含：

```python
@dataclass
class ImportResult:
    sessions: list[ImportedSession]
    turns: list[ImportedTurn]
    tool_events: list[ImportedToolEvent]
    entries: list[ImportedEntry]
    warnings: list[str]
```

---

## 8. Codex JSONL Importer 详细设计

这是第一版最关键 importer。

### 8.1 输入格式判断

Codex JSONL 样本特点：

- 文件是 `.jsonl`
- 每一行是一个 JSON object
- 顶层字段通常有：
  - `timestamp`
  - `type`
  - `payload`

样本中出现的顶层 `type`：

```text
session_meta
turn_context
event_msg
response_item
```

样本统计：

```text
总行数：345
session_meta：1
turn_context：3
event_msg：107
response_item：234
```

event_msg 中常见 payload type：

```text
task_started
user_message
agent_message
patch_apply_end
task_complete
token_count
```

注意：`response_item` 数量最多，但第一版不应该重点处理它。  
很多 response_item 包含系统消息、工具调用细节、模型内部输出或上下文内容。第一版只在必要时提取少量工具信息。

### 8.2 Codex importer 的目标

Codex importer 不追求完整还原会话。  
它只要提取：

1. 这次 Codex 会话属于哪个项目。
2. 用户每轮让 Codex 做了什么。
3. Codex 每轮最终完成了什么。
4. 是否修改了文件。
5. 是否运行了测试或 build。
6. 是否有重要错误。
7. 是否留下待办或建议。
8. 这些内容是否值得 LLM 进一步整理成 Life Tracer 记录。

### 8.3 必须提取的信息

#### A. session_meta

从 `type == "session_meta"` 的 payload 提取：

```text
id
timestamp
cwd
originator
cli_version
source
model_provider
```

从 cwd 推断：

```text
project_path = cwd
project_name = cwd 最后一级目录
```

例如：

```text
cwd = /root/workspace/job/calculus_area_viewer
project_name = calculus_area_viewer
```

保存到 `sessions` 表。

#### B. turn_context

`turn_context` 里有：

```text
turn_id
cwd
current_date
timezone
approval_policy
sandbox_policy
```

第一版只需要：

```text
turn_id
cwd
current_date
timezone
```

不要把完整 sandbox policy 展示给用户。  
可以存入 metadata_json，但不展示。

#### C. user_message

从：

```json
{
  "type": "event_msg",
  "payload": {
    "type": "user_message",
    "message": "..."
  }
}
```

提取用户任务。

一个 user_message 通常对应一个 turn。  
如果 payload 里没有 turn_id，可以用时间顺序配对最近的 task_started / turn_context。

#### D. task_complete

从：

```json
{
  "type": "event_msg",
  "payload": {
    "type": "task_complete",
    "turn_id": "...",
    "last_agent_message": "...",
    "completed_at": ...,
    "duration_ms": ...,
    "time_to_first_token_ms": ...
  }
}
```

提取 Codex 最终总结。

`last_agent_message` 是第一版最重要内容。  
它通常比中间 agent_message 更干净，更适合 Life Tracer。

#### E. patch_apply_end

从：

```json
{
  "payload": {
    "type": "patch_apply_end",
    "turn_id": "...",
    "stdout": "Success. Updated the following files...",
    "stderr": "",
    "success": true,
    "changes": {
      "/path/to/file": {
        "type": "update",
        "unified_diff": "..."
      }
    }
  }
}
```

提取：

```text
turn_id
success
changed file paths
change type
stdout excerpt
stderr excerpt
```

不要把完整 unified_diff 展示在主页面。  
可以不保存 diff，或者只保存到 raw refs。  
如果保存 diff，也不要进入普通记录流。

#### F. function_call / function_call_output / exec output

第一版只提取重要信息：

- 命令文本，如果容易识别。
- 是否失败。
- 是否包含测试结果。
- 是否包含 build 结果。
- 是否包含 audit 结果。
- 输出摘要前 500-1000 字符。

不要完整保存每一个命令输出到主记录。  
完整内容已经在 raw import 里。

### 8.4 turn 配对逻辑

Codex JSONL 不是简单 user / assistant 结构。  
需要把事件流重组成 turns。

推荐配对逻辑：

1. 按 JSONL 行顺序读取。
2. 记录每一行的 line_number。
3. 遇到 `task_started`：
   - 新建 current_turn。
   - 如果 payload 有 turn_id，记录。
4. 遇到 `turn_context`：
   - 如果有 turn_id，更新 current_turn。
5. 遇到 `user_message`：
   - 绑定到 current_turn。
   - 如果没有 current_turn，则新建一个 inferred_turn。
6. 遇到 `task_complete`：
   - 根据 turn_id 找 turn。
   - 写入 final_summary、completed_at、duration_ms。
   - 标记 turn 完成。
7. 遇到 `patch_apply_end`：
   - 根据 turn_id 绑定 tool event。
8. 遇到其他工具输出：
   - 尝试根据 turn_id 绑定。
   - 如果没有 turn_id，绑定到最近未完成 turn。
9. 一个 turn 最终至少应该有：
   - turn_index
   - user_request
   - final_summary
   - raw_line_start
   - raw_line_end

### 8.5 从样本导出的 turn records

样本中应该提取出 3 个核心 turn：

#### Turn 1：检查当前项目状态并提出优化计划

user_request：

```text
ok. check the current folder. have a look at its current status. give your understanding. and suggest a plan for optimization.
```

final_summary 重点：

```text
项目是一个 Vite/React calculus area/volume viewer。
不是 git repo。
node_modules 和 dist 已存在。
src 是主要源码。
production build 成功。
Vite 警告 JS chunk 很大。
识别到一个 chart data shape bug。
提出优化计划，包括修正 chart data、处理 NaN/singularity、优化 bundle、lazy-load heavy visualization、修复 Three.js lifecycle、增加 tests。
```

分类建议：

```text
Coding / ProjectInspection
```

#### Turn 2：判断项目是否臃肿并执行优化

user_request：

```text
check whether this project is臃肿, if not you can start your optimization. also doyou have any suggestions? if yes, try and test.
```

final_summary 重点：

```text
确认项目臃肿。
主要问题是 plotly.js-dist-min。
替换 Plotly 2D chart 为 lightweight SVG chart。
移除 plotly.js-dist-min。
mathjs 改为 mathjs/number。
lazy-load 3D view。
修复 chart data shape bug。
修复 uploaded-data integration。
增加 Three.js cleanup。
增加测试。
build 从 33.12s 降到 6.27s。
dist 从 5.7M 降到 980K。
npm test 7 passed。
npm run build passed。
npm audit --omit=dev 0 production vulnerabilities。
```

分类建议：

```text
Coding / Optimization
```

这是最有价值的一条 Codex work session 记录。

#### Turn 3：解释如何在 VPS 上测试结果

user_request：

```text
how to test and see the results on vps?
```

final_summary 重点：

```text
cd 到项目目录。
运行 npm test。
运行 npm run build。
运行 npm run preview -- --host 0.0.0.0 --port 4173。
手机或浏览器打开 http://YOUR_VPS_IP:4173。
如果端口阻塞，用 ufw allow 4173/tcp。
开发模式可以用 npm run dev -- --host 0.0.0.0 --port 5173。
生产预览用于检查 bundle/performance，dev mode 用于编辑。
```

分类建议：

```text
Coding / DeploymentInstruction
```

### 8.6 Codex importer 不应该提取什么

第一版不要提取：

- 每一个 token_count。
- 完整 base_instructions。
- 完整 developer message。
- encrypted reasoning。
- 每一个 agent_message 的中间过程。
- 每一个 function_call 的完整 raw payload。
- 每一个 diff 的全部内容。
- 每一个 stdout/stderr 的完整内容。
- sandbox policy 全量展示。
- rate limit 信息。
- 模型上下文窗口信息。

这些内容可以保存在 raw import 中，或少量存在 metadata_json 中，但不要进入用户日常记录页面。

### 8.7 Codex importer 应该生成的对象

#### ImportedSession

```json
{
  "source_type": "codex",
  "source_session_id": "019e149d-8711-7433-8210-f096fc37e797",
  "project_name": "calculus_area_viewer",
  "project_path": "/root/workspace/job/calculus_area_viewer",
  "started_at": "2026-05-11T01:18:48.596Z",
  "originator": "codex-tui",
  "cli_version": "0.130.0",
  "model_provider": "openai"
}
```

#### ImportedTurn

```json
{
  "source_type": "codex",
  "turn_index": 2,
  "source_turn_id": "019e14a2-ca3f-7fa2-821e-a85105140ce0",
  "project_name": "calculus_area_viewer",
  "user_request": "check whether this project is臃肿...",
  "final_summary": "Yes, it was bloated...",
  "duration_ms": 589923,
  "llm_status": "pending"
}
```

#### ImportedToolEvent

```json
{
  "event_type": "patch_apply_end",
  "source_turn_id": "019e14a2-ca3f-7fa2-821e-a85105140ce0",
  "success": true,
  "changed_files": [
    "src/utils/numericalIntegrator.js",
    "src/App.jsx",
    "src/components/FunctionInput.jsx"
  ],
  "output_excerpt": "Success. Updated the following files..."
}
```

### 8.8 Codex importer 的输出页面

导入完成后，`/import/{id}` 页面应该显示：

```text
Codex Session: calculus_area_viewer
Started: 2026-05-11
Path: /root/workspace/job/calculus_area_viewer
Turns: 3
Tool events: 重要 patch/apply/build/test events 若干

Turn 1: Project inspection
User request: ...
Codex result: ...
[Organize this turn]

Turn 2: Optimization
User request: ...
Codex result: ...
Changed files: src/App.jsx, src/utils/numericalIntegrator.js, ...
[Organize this turn]

Turn 3: VPS testing
User request: ...
Codex result: ...
[Organize this turn]
```

### 8.9 Codex importer 的 Markdown 导出

导出某个 Codex session 时，Markdown 应该像这样：

```markdown
# Codex Session: calculus_area_viewer

Date: 2026-05-11
Source: codex-tui
Path: /root/workspace/job/calculus_area_viewer

## Turn 1: Project inspection

### User request

...

### Codex result

...

## Turn 2: Optimization

### User request

...

### Codex result

...

### Key changed files

- src/App.jsx
- src/utils/numericalIntegrator.js
- src/components/AreaChart2D.jsx

### Verification

- npm test: passed
- npm run build: passed

## Turn 3: VPS testing

...
```

---

## 9. Markdown / JSON / pasted text importer

第一版重点是 Codex JSONL，但要预留普通 importer。

### 9.1 Markdown importer

功能：

- 保存原始 Markdown。
- 尝试按标题切分。
- 如果没有标题，按空行或长度切分。
- 每段变成 ImportedEntry。
- LLM 后续判断分类。

不要过度解析 Markdown 语法。

### 9.2 JSON importer

功能：

- 保存原始 JSON。
- 判断是否是数组、对象、chat messages。
- 如果发现 `messages`、`role`、`content`，按聊天记录导入。
- 如果无法识别，作为 raw JSON 保存，并创建一条 Reference 记录。

### 9.3 pasted text importer

功能：

- 用户直接粘贴一大段文本。
- 保存原文。
- 按段落初步切分。
- 生成若干 entries 或一个 raw import。
- 用户手动触发 LLM 整理。

---

## 10. LLM 整理设计

### 10.1 LLM 的地位

LLM 是整理层，不是存储层。  
系统没有 LLM 也必须能写入、导入、搜索、导出。

### 10.2 支持 provider

第一版支持：

```text
OpenRouter
MiniMax
```

并预留：

```text
MockProvider
```

MockProvider 用于没有 API key 时测试页面和流程。

### 10.3 LLM 配置

`.env`：

```env
APP_PASSWORD=change_me

LLM_PROVIDER=openrouter
LLM_MODEL=
LLM_API_KEY=

# or
# LLM_PROVIDER=minimax
# LLM_MODEL=
# LLM_API_KEY=
```

### 10.4 LLM 输出必须是 JSON

不要让 LLM 输出散文。  
所有整理任务都要求返回 JSON。

通用输出字段：

```json
{
  "summary": "",
  "category": "",
  "secondary_category": "",
  "is_life_insight": false,
  "life_insight_reason": "",
  "tags": [],
  "action_items": [],
  "open_questions": [],
  "related_project": "",
  "cleaned_text": ""
}
```

### 10.5 分类体系

第一版固定分类：

```text
LifeInsight
WorkLog
ResearchIdea
Teaching
Coding
SystemDesign
Finance
Family
Health
Question
Decision
ActionItem
Reference
Other
```

### 10.6 LifeInsight 的判断标准

LifeInsight 指的是：

- 自我理解。
- 长期原则。
- 方法论。
- 对生活、工作方式、判断过程的抽象认识。
- 不是简单事件。
- 不是单纯技术步骤。
- 不是普通待办。

例子：

```text
我发现我不是缺少工具，而是缺少稳定记录和复盘的结构。
```

应该是：

```json
{
  "category": "LifeInsight",
  "secondary_category": "PersonalWorkflow",
  "is_life_insight": true
}
```

例子：

```text
FastAPI + SQLite 可以先完成记录入口，不需要 Docker。
```

应该是：

```json
{
  "category": "SystemDesign",
  "secondary_category": "MVPArchitecture",
  "is_life_insight": false
}
```

### 10.7 Codex turn 的 LLM prompt

用于整理 session_turn：

```text
你正在整理一条 Codex 工作会话记录。

输入包括：
- project_name
- user_request
- codex_final_summary
- important_changed_files
- important_tool_events

请只根据输入内容整理，不要编造。

返回 JSON，字段如下：

{
  "summary": "用中文简洁总结这轮工作完成了什么",
  "category": "Coding / SystemDesign / ResearchIdea / Teaching / LifeInsight / Other 之一",
  "secondary_category": "更细的英文或中文分类",
  "is_life_insight": true 或 false,
  "life_insight_reason": "如果是人生感悟，说明原因；否则为空字符串",
  "technical_result": "如果是技术工作，总结具体技术结果",
  "changed_files": ["..."],
  "verification": ["测试或 build 结果"],
  "action_items": ["后续要做的事情"],
  "open_questions": ["仍然没解决的问题"],
  "tags": ["标签"],
  "cleaned_text": "可以放入 Markdown 归档的整理版文本"
}

分类规则：
- 如果主要是在改代码、部署、测试、排错，category 用 Coding。
- 如果主要是在设计系统结构、模块边界、MVP，category 用 SystemDesign。
- 如果内容抽象出用户长期工作方式、生活原则、判断原则，才用 LifeInsight。
- 不要把普通技术步骤误判为人生感悟。
- 如果一条技术记录里包含抽象方法论，可以 category 用 Coding，同时 is_life_insight=true。
```

### 10.8 手动整理流程

用户点击：

```text
[Organize this entry]
[Organize this turn]
[Summarize today]
```

系统才调用 LLM。

流程：

```text
读取目标内容
构造 prompt
调用 provider
解析 JSON
写入 llm_outputs
更新 entries/session_turns 的 llm_status
页面展示结果
```

如果 LLM 返回无效 JSON：

1. 保存 raw output 到 error。
2. 页面提示失败。
3. 不覆盖任何已有整理结果。
4. 用户可以重试。

---

## 11. 搜索和展示策略

### 11.1 搜索

第一版用 SQLite LIKE 即可，不需要全文搜索引擎。

搜索范围：

- entries.raw_content
- entries.normalized_content
- session_turns.user_request
- session_turns.final_summary
- llm_outputs.summary
- llm_outputs.output_json

后续可升级 SQLite FTS5，但第一版不必做。

### 11.2 Today 页面排序

排序建议：

1. 手动 entries 按 created_at。
2. 导入 sessions 按 started_at 或 imported_at。
3. 如果同一天混合显示，给来源打标：

```text
[Manual]
[Codex]
[ClaudeCode]
[Import]
```

### 11.3 不要让工具日志污染日常页面

tool_events 默认不出现在 `/today` 主列表。  
只有进入 session detail 时，才显示简化后的 changed files / verification / important errors。

---

## 12. 导出设计

### 12.1 JSONL 导出

每一行一个对象。  
适合以后再导入、交给 LLM、用 Python 分析。

示例：

```json
{"type":"entry","id":1,"created_at":"2026-05-15T10:00:00","record_type":"Thought","raw_content":"...","category":"LifeInsight"}
```

session turn 示例：

```json
{"type":"session_turn","session_id":1,"turn_index":2,"project_name":"calculus_area_viewer","user_request":"...","summary":"...","category":"Coding"}
```

### 12.2 Markdown 导出

每日导出：

```markdown
# 2026-05-15

## Manual Records

### 10:30 Thought

原文...

LLM summary...

## Codex Sessions

### calculus_area_viewer

#### Turn 2: Optimization

User request...

Result...

Changed files...

Action items...
```

### 12.3 备份

`scripts/backup.sh`：

```bash
#!/usr/bin/env bash
set -e

DATE=$(date +%Y-%m-%d_%H-%M-%S)
mkdir -p data/backups
sqlite3 data/tracer.sqlite ".backup data/backups/tracer-$DATE.sqlite"
```

不要直接在数据库写入中复制文件。  
使用 sqlite `.backup` 更安全。

---

## 13. 安全设计

### 13.1 第一版使用简单密码

`.env`：

```env
APP_PASSWORD=your_password
```

访问时：

- 未登录进入 `/login`
- 输入密码
- session cookie 记录登录状态

### 13.2 不要裸奔公网

即使用 Quick Tunnel，也要有密码。  
这个系统会存私人记录、工作记录、路径、可能的 API 调用结果，不能公开访问。

### 13.3 API Key 不进数据库

LLM API Key 只放 `.env`。  
不要写入 SQLite。  
不要导出到 Markdown。  
不要展示在页面上。

---

## 14. 无域名 HTTPS 访问方案

用户没有域名，也暂时不想买。

### 14.1 第一阶段：Cloudflare Quick Tunnel

运行方式大致是：

```bash
cloudflared tunnel --url http://localhost:8010
```

它会生成一个临时 HTTPS 地址：

```text
https://random-words.trycloudflare.com
```

手机打开这个地址即可访问 VPS 上的 Life Tracer。

注意：

- 这是临时地址。
- 重启 tunnel 后地址可能变化。
- 适合 MVP 测试。
- 不适合长期稳定入口。

### 14.2 第二阶段可选：Tailscale Funnel

如果用户愿意注册 Tailscale，可以考虑更稳定的免费入口。  
但第一版不要求实现。

### 14.3 暂时不使用 GitHub Pages / Vercel

原因：

- GitHub Pages 只能放静态页面，不能直接写 SQLite。
- Vercel 可做前端，但后端仍在 VPS，会引入 CORS、认证、API 地址和双端部署。
- 第一版应该保持单体 FastAPI 应用。

---

## 15. MVP 开发顺序

Codex 应该按这个顺序实现，不要跳到复杂功能。

### Phase 1：项目骨架

1. 创建 FastAPI 项目。
2. 创建 SQLite 初始化脚本。
3. 创建 `.env.example`。
4. 创建基础 layout.html 和 style.css。
5. 创建登录保护。
6. 创建首页 `/`。

完成后应该能：

```text
启动服务
打开网页
登录
看到输入框
```

### Phase 2：手动记录

1. 实现 entries 表。
2. 实现新增记录。
3. 实现 today 页面。
4. 实现 search 页面基础搜索。

完成后应该能：

```text
手机输入一句话
保存到 SQLite
今天页面看到
搜索能搜到
```

### Phase 3：Codex JSONL 导入

1. 实现 raw_imports 表。
2. 实现上传 JSONL。
3. 保存 raw file。
4. 实现 codex_jsonl.py。
5. 解析 session_meta。
6. 解析 user_message。
7. 解析 task_complete。
8. 配对成 session_turns。
9. 抽取 patch_apply_end 的 changed_files。
10. import detail 页面展示 session + turns。

完成后应该能：

```text
上传 Codex JSONL
看到项目名
看到 3 个 turn
每个 turn 有 user request 和 final summary
看到关键 changed files
```

### Phase 4：LLM provider

1. 实现 llm/base.py。
2. 实现 OpenRouter provider。
3. 实现 MiniMax provider。
4. 实现 MockProvider。
5. 实现 organize_turn。
6. 实现 organize_entry。
7. 结果保存到 llm_outputs。

完成后应该能：

```text
点击整理某条 entry
点击整理某个 Codex turn
看到 category、summary、tags、action_items、is_life_insight
```

### Phase 5：导出和备份

1. 导出 daily Markdown。
2. 导出 session Markdown。
3. 导出全部 JSONL。
4. 实现 backup.sh。
5. 页面上提供手动备份按钮。

完成后应该能：

```text
下载 Markdown
下载 JSONL
创建 SQLite backup
```

### Phase 6：Quick Tunnel 运行说明

1. README 写 Debian 部署步骤。
2. systemd service 示例。
3. cloudflared quick tunnel 示例。
4. 手机访问说明。
5. 安全提醒。

---

## 16. Codex 实现时的硬性要求

1. 不要使用 Docker。
2. 不要引入 React。
3. 不要引入 PostgreSQL。
4. 不要引入 Redis。
5. 不要做复杂前端构建。
6. 不要把 LLM 自动绑定到每次保存。
7. 不要删除原始导入文件。
8. 不要让 LLM 覆盖 raw_content。
9. 不要把完整 Codex tool trace 塞进 today 页面。
10. 不要解析 encrypted reasoning。
11. 不要展示完整 base_instructions。
12. 不要一开始做所有 importer，只先做好 Codex JSONL。
13. 所有重要操作要有清楚错误提示。
14. 所有文件写入必须进入 `data/`。
15. 所有路径要相对项目根目录，不要写死 `/root/...`。
16. 页面要适合手机窄屏。
17. Python 依赖要尽量少。
18. 所有 LLM JSON 解析失败时不能破坏已有数据。
19. 导入器要可重跑。
20. README 要能让用户在 Debian 2GB VPS 上照着部署。

---

## 17. README 中必须包含的命令

### 17.1 创建环境

```bash
sudo apt update
sudo apt install -y python3-venv sqlite3

cd ~/life-tracer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 17.2 初始化数据库

```bash
python scripts/init_db.py
```

### 17.3 本地启动

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8010
```

### 17.4 Quick Tunnel

```bash
cloudflared tunnel --url http://localhost:8010
```

### 17.5 systemd 示例

```ini
[Unit]
Description=Life Tracer
After=network.target

[Service]
User=YOUR_USER
WorkingDirectory=/home/YOUR_USER/life-tracer
EnvironmentFile=/home/YOUR_USER/life-tracer/.env
ExecStart=/home/YOUR_USER/life-tracer/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8010
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 18. 第一版验收标准

### 18.1 手动记录验收

- 打开首页。
- 输入中文夹英文记录。
- 保存。
- today 页面能看到。
- search 能搜到。
- Markdown 导出包含该记录。

### 18.2 Codex 导入验收

使用样本：

```text
rollout-2026-05-11T01-18-48-019e149d-8711-7433-8210-f096fc37e797.jsonl
```

导入后应识别：

```text
session_meta：1
turns：3
project_name：calculus_area_viewer
```

应提取 3 个 user_request：

```text
1. check the current folder...
2. check whether this project is臃肿...
3. how to test and see the results on vps?
```

应提取 3 个 task_complete final_summary。

第二个 turn 应能显示：

```text
项目臃肿点：plotly.js-dist-min
优化结果：移除 Plotly 2D chart，改 lightweight SVG
build 时间：33.12s → 6.27s
dist：5.7M → 980K
npm test：7 passed
npm run build：passed
```

### 18.3 LLM 整理验收

对第二个 Codex turn 点击整理后，应生成类似：

```json
{
  "summary": "这轮 Codex 工作确认 calculus_area_viewer 的主要臃肿来源是 plotly.js-dist-min，并通过替换为轻量 SVG 图表、移除依赖、lazy-load 3D view、修复积分和图表数据问题，使 build 时间和 dist 体积明显下降。",
  "category": "Coding",
  "secondary_category": "FrontendOptimization",
  "is_life_insight": false,
  "technical_result": "build 33.12s -> 6.27s, dist 5.7M -> 980K",
  "action_items": ["后续如有需要，可处理 Vite/esbuild dev dependency audit 问题"],
  "tags": ["codex", "optimization", "vite", "react", "bundle-size"]
}
```

### 18.4 LifeInsight 验收

手动输入：

```text
我发现我不是缺少工具，而是缺少稳定记录和复盘的结构。
```

点击整理后应识别为：

```json
{
  "category": "LifeInsight",
  "is_life_insight": true
}
```

手动输入：

```text
FastAPI + SQLite 可以先完成记录入口，不需要 Docker。
```

点击整理后不应误判为人生感悟，应更接近：

```json
{
  "category": "SystemDesign",
  "is_life_insight": false
}
```

---

## 19. 未来扩展方向

第一版完成后，再考虑：

1. Claude Code importer。
2. ChatGPT export importer。
3. SQLite FTS5 全文搜索。
4. 每周总结。
5. 项目维度页面。
6. 学生/教学记录维度页面。
7. 研究想法维度页面。
8. 简单任务追踪。
9. 本地 LLM 或低价模型批处理。
10. 长期 LifeInsight 回顾。

但这些都不属于第一版。

---

## 20. 最终一句话

这个项目第一版的目标不是做一个漂亮笔记软件，而是做一个轻量、可迁移、能导入工作会话、能手动调用 LLM 整理的私人 Life Tracer。

最重要的三件事：

```text
1. 原始数据不丢。
2. 导入器只提取最重要信息，不把工具日志污染人生记录。
3. LLM 整理结果可重跑、可替换、可导出。
```
