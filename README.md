# 🖥️ DPOS — Desktop Personal OS

<div align="center">

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![UI Framework](https://img.shields.io/badge/UI-PyQt6-green.svg?style=for-the-badge&logo=qt&logoColor=white)](https://www.qt.io)
[![Database](https://img.shields.io/badge/Database-SQLAlchemy%20%2B%20SQLite-orange.svg?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

</div>

---

### 🌟 Marketing Motto
> **Your Desktop, Reimagined.**  
> *A lightning-fast, AI-integrated Personal OS designed to consolidate your search, automate your workflows, and manage your cognitive load — keeping you in flow state, locally and securely.*

### 🛠️ Developer Motto
> **Build for speed, isolate for sanity.**  
> *Every module a silent engine, every service a controlled thread, communicating via clean events to construct a unified, unbreakable user experience.*

---

## 🚀 Key Features

*   🔍 **Universal Search** — Instantly scan and find your files, clipboard history, screen OCR text, or commands via a supercharged Whoosh query index.
*   📋 **Smart Clipboard** — A background monitor categorizes text copies (SQL, URLs, security tokens, source code, text) to surface them right when you need them.
*   📁 **Workspace Launcher** — Create and orchestrate custom template environments (like FastAPI, React/Node) with a single-click subprocess setup.
*   ⚙️ **Automation Studio** — Record, playback, and schedule macro-sequences (cron-style) to automate repetitive desktop steps.
*   🧠 **Developer Memory** — Hooks terminals, git tracking, and file edits into a local SQLite store so you can review what you did and recall details.
*   📸 **Screenshot Intelligence** — Captures screenshots on the fly, runs PyTesseract OCR, and instantly indexes the extracted text into universal search.
*   📊 **System Health Monitor** — Tracks CPU/RAM logs, threshold triggers, active ports, and container health status via docker-py.
*   🤖 **Local AI** — Local Ollama API context assembly translates developer memory + search context into locally executable actions.

---

## 📐 Clean Architecture Guidelines

To ensure DPOS remains stable, fast, and modular, developers must follow three strict architectural boundaries:

### 1. Module Isolation
*   Every folder in `modules/` is fully self-contained.
*   Modules can import **only** from `core/` and `utils/`.
*   They **never** import from the `ui/` layer or other modules. All cross-module communication goes through `core/events.py`.

### 2. Service Layer
*   `services/` is the single source for background thread executions.
*   Modules expose plain, synchronous Python classes; background services wrap them in QThreads or system threads and register them in `service_manager.py`.

### 3. UI → Module Boundary
*   For **reads/queries** (fast, sync), UI widgets call module classes directly.
*   For **writes/actions** (side effects, slow logic), UI emits a decoupled event via the `core/events.py` bus. The corresponding module listens and acts.

---

## 📂 Project Structure

<details>
<summary><b>🔍 Expand to view the Production Folder Tree</b></summary>

```
dpos/
│
├── main.py                          # App entry point — boots everything
├── app.py                           # App class — wires all modules together
├── config.py                        # Global constants, paths, env config
├── requirements.txt                 # All pip dependencies
├── requirements-dev.txt             # Dev-only deps (pytest, black, mypy)
├── pyproject.toml                   # Project metadata, tool config
├── .env.example                     # Env var template (no secrets)
├── README.md
│
├── core/                            # Engine — no UI, no side effects
│   ├── __init__.py
│   ├── database.py                  # SQLAlchemy engine, session factory
│   ├── models.py                    # All ORM models (Project, Task, Clip, etc.)
│   ├── migrations/                  # Alembic migration scripts
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── 001_initial_schema.py
│   ├── events.py                    # In-process event bus (pub/sub)
│   └── exceptions.py               # Custom exception classes
│
├── modules/                         # Feature modules — one folder per feature
│   │
│   ├── search/                      # Universal search
│   │   ├── __init__.py
│   │   ├── indexer.py               # Whoosh index writer
│   │   ├── searcher.py              # Query engine, result ranking
│   │   ├── schema.py                # Whoosh field schemas
│   │   └── providers/              # What gets indexed
│   │       ├── __init__.py
│   │       ├── file_provider.py     # Files + code
│   │       ├── clip_provider.py     # Clipboard history
│   │       ├── screenshot_provider.py
│   │       └── command_provider.py  # Terminal commands
│   │
│   ├── clipboard/                   # Smart clipboard
│   │   ├── __init__.py
│   │   ├── monitor.py               # pyperclip poll loop (background thread)
│   │   ├── store.py                 # Save, retrieve, tag clips
│   │   └── categories.py           # SQL, URL, token, code, text detection
│   │
│   ├── workspace/                   # Workspace launcher
│   │   ├── __init__.py
│   │   ├── launcher.py              # subprocess orchestrator
│   │   ├── registry.py              # CRUD for saved workspaces
│   │   └── templates/              # Built-in workspace templates
│   │       ├── python_fastapi.json
│   │       └── react_node.json
│   │
│   ├── automation/                  # Automation studio
│   │   ├── __init__.py
│   │   ├── recorder.py              # Record user action sequences
│   │   ├── runner.py                # Execute saved automation scripts
│   │   ├── scheduler.py             # schedule-based cron runner
│   │   └── scripts/                # User-saved automations (JSON)
│   │       └── .gitkeep
│   │
│   ├── memory/                      # Developer memory
│   │   ├── __init__.py
│   │   ├── capture.py               # Hook terminal, file edits, git
│   │   ├── store.py                 # Save memories to SQLite
│   │   └── recall.py                # Query + surface relevant memories
│   │
│   ├── projects/                    # Project dashboard
│   │   ├── __init__.py
│   │   ├── manager.py               # CRUD for projects
│   │   ├── git_watcher.py           # watchdog — git status, changes
│   │   └── service_checker.py       # Poll ports, Docker containers
│   │
│   ├── screenshots/                 # Screenshot intelligence
│   │   ├── __init__.py
│   │   ├── watcher.py               # watchdog — detect new screenshots
│   │   ├── ocr.py                   # pytesseract text extraction
│   │   └── indexer.py               # Push OCR text to search index
│   │
│   ├── monitor/                     # System health monitor
│   │   ├── __init__.py
│   │   ├── collector.py             # psutil CPU, RAM, disk, ports
│   │   ├── docker_watcher.py        # docker-py container status
│   │   └── alerts.py                # Thresholds, alert emission
│   │
│   └── ai/                          # Local AI
│       ├── __init__.py
│       ├── client.py                # Ollama HTTP client wrapper
│       ├── prompts.py               # Prompt templates (explain, generate, summarize)
│       └── context_builder.py       # Assemble context from memory + search
│
├── ui/                              # All PyQt6 UI code
│   ├── __init__.py
│   ├── app_window.py                # Main QMainWindow
│   ├── system_tray.py               # QSystemTrayIcon, tray menu
│   ├── hotkeys.py                   # Global keyboard hooks (keyboard lib)
│   │
│   ├── command_center/             # Ctrl+Space overlay
│   │   ├── __init__.py
│   │   ├── widget.py                # Command palette QWidget
│   │   ├── input_bar.py             # Search input + live results
│   │   └── result_list.py           # Result rows, icons, keyboard nav
│   │
│   ├── dashboard/                   # Daily dashboard panel
│   │   ├── __init__.py
│   │   ├── widget.py
│   │   ├── stats_card.py            # Reusable stat card component
│   │   └── greeting.py              # Time-aware greeting text
│   │
│   ├── projects/                    # Project panel
│   │   ├── __init__.py
│   │   ├── panel.py
│   │   ├── project_card.py
│   │   └── service_badge.py         # Running/stopped service pill
│   │
│   ├── clipboard/                   # Clipboard panel
│   │   ├── __init__.py
│   │   ├── panel.py
│   │   └── clip_item.py
│   │
│   ├── monitor/                     # System monitor panel
│   │   ├── __init__.py
│   │   ├── panel.py
│   │   └── gauge.py                 # CPU/RAM arc gauge widget
│   │
│   ├── automation/                  # Automation studio panel
│   │   ├── __init__.py
│   │   ├── panel.py
│   │   └── step_editor.py
│   │
│   ├── settings/                    # Settings panel
│   │   ├── __init__.py
│   │   └── panel.py
│   │
│   ├── components/                  # Shared reusable widgets
│   │   ├── __init__.py
│   │   ├── badge.py
│   │   ├── icon_button.py
│   │   ├── loading_spinner.py
│   │   └── empty_state.py
│   │
│   └── styles/                      # QSS stylesheets
│       ├── base.qss                 # Global theme variables
│       ├── dark.qss
│       └── light.qss
│
├── services/                        # Background services (long-running threads)
│   ├── __init__.py
│   ├── service_manager.py           # Start/stop/restart all services
│   ├── clipboard_service.py         # Wraps modules/clipboard/monitor.py
│   ├── file_watcher_service.py      # Wraps watchdog for files + screenshots
│   ├── monitor_service.py           # Wraps modules/monitor/collector.py
│   └── scheduler_service.py         # Wraps modules/automation/scheduler.py
│
├── utils/                           # Pure helpers — zero business logic
│   ├── __init__.py
│   ├── file_utils.py                # Path helpers, extension detection
│   ├── process_utils.py             # subprocess wrappers, port checkers
│   ├── time_utils.py                # Human-readable time, relative dates
│   ├── text_utils.py                # Truncate, highlight, sanitize
│   └── platform.py                  # OS detection, platform-specific paths
│
├── data/                            # Runtime data (gitignored)
│   ├── dpos.db                      # SQLite database
│   ├── search_index/               # Whoosh index files
│   └── logs/
│       ├── app.log
│       └── error.log
│
├── assets/                          # Static assets (committed)
│   ├── icons/
│   │   ├── tray_icon.png
│   │   └── app_icon.ico
│   └── fonts/
│
└── tests/                           # Test suite
    ├── __init__.py
    ├── conftest.py                  # Fixtures, test DB setup
    ├── unit/
    │   ├── test_clipboard.py
    │   ├── test_search.py
    │   ├── test_workspace.py
    │   └── test_memory.py
    └── integration/
        ├── test_db.py
        └── test_services.py
```

</details>

---

## ⚙️ Getting Started

### Prerequisites
- Python `3.10` or higher.
- Tesseract OCR (for screenshot text scanning).

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/sandyddeveloper/DPOS.git
   cd DPOS
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   # For development:
   pip install -r requirements-dev.txt
   ```

### Running the App

You can launch DPOS in one of two ways. Running either command will automatically initialize the database (and seed it with mock projects/tasks if run for the first time), start all background thread monitors, and display the PyQt6 frameless dashboard.

#### Option 1: Direct Script Execution
```bash
python main.py
```

#### Option 2: Installed CLI Command
1. Install the application in editable/development mode:
   ```bash
   pip install -e .
   ```
2. Execute the unified CLI command directly from any terminal session:
   ```bash
   dpos
   ```

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.