# Cindergrace Git GUI (Tkinter)

Lightweight Git GUI for everyday tasks: profiles, staging, history, and AI commit messages.

## License
PolyForm Noncommercial 1.0.0

## Features
- Select repository folder
- Git status, pull, push, log
- Fetch and rebase
- Stash + stash pop
- Refresh branches and checkout (local + remote)
- Create/delete branches
- Stage all + commit with message
- Favorites list (save/load repo paths)
- Profiles (repo path + branch + remote)
- Clone repository (URL + destination)
- Auth check (git user config + SSH key presence)
- History panel (last 50 commits)
- Diff summary (changed files + diff --stat)
- OpenRouter commit message suggestions (encrypted API key)

## Architecture
- `main.py`: Tkinter UI
- `git_ops.py`: Git command helpers
- `storage.py`: JSON persistence
- `openrouter.py`: OpenRouter + encryption helpers
- `prompt_builder.py`: Commit prompt formatting

## Profiles
Profiles are stored in `~/.cindergrace_git_gui_profiles.json`.
Each profile stores:
- repo path
- default branch
- remote name

## OpenRouter setup
The API key is stored encrypted at `~/.cindergrace_git_gui_openrouter.json`.
You unlock it once per session with a password.

Dependencies:
```bash
python3 -m pip install cryptography requests
```

## Tests
```bash
python3 -m pytest -q
```

## Install (editable)
```bash
python3 -m pip install -e .[dev]
```

## Run
```bash
./start.sh
```

With refresh:
```bash
./start.sh --refresh
```

Runtime-only install:
```bash
./start.sh --no-dev
```

Windows:
```bat
start.bat
```

## Notes
If Git requires credentials, configure a credential helper or authenticate via terminal.
Favorites are stored in `~/.cindergrace_git_gui_favorites.json`.
