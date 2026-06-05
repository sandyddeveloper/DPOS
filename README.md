# DPOS — Desktop Personal OS

> **Marketing Motto:**  
> *Your Desktop, Reimagined. A lightning-fast, AI-integrated Personal OS designed to consolidate search, automate workflows, and manage your cognitive load — keeping you in flow state, locally and securely.*

> **Developer Motto:**  
> *Build for speed, isolate for sanity. Every module a silent engine, every service a controlled thread, communicating via clean events to construct a unified, unbreakable user experience.*

---

## Production Folder Structure

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

---

## Key Design Rules

### Module isolation
Each folder in `modules/` is self-contained. It only imports from `core/` and `utils/`.
It never imports from `ui/` or another module directly — communication goes through `core/events.py`.

### Service layer
`services/` are the only things that run background threads. Modules expose plain Python classes;
services wrap them in threads and register with `service_manager.py`.

### UI → Module boundary
UI code calls module functions directly for reads (fast, sync).
For writes and side effects, UI emits an event via `core/events.py` — the module listens and responds.

### Data directory
`data/` is gitignored. The app creates it on first run. Never hardcode paths — use `config.py`.

---

## Startup flow

```
main.py
  └── app.py (App.__init__)
        ├── core/database.py  →  create tables if not exist
        ├── services/service_manager.py  →  start all background threads
        ├── ui/app_window.py  →  build main window
        └── ui/hotkeys.py  →  register Ctrl+Space global hook
```