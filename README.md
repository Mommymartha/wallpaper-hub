# Windows Fleet Wallpaper Manager

Cloud-Hub architecture: a GitHub repo hosts `config.json` (a version counter)
and `wallpaper.jpg`. A local **Controller** pushes updates via the GitHub
REST API. A **Client Agent** on each target machine polls the public raw
URL every 60 seconds and applies changes with the Win32 API.

## 1. One-time GitHub setup

1. Create a repository (public or private) to act as the hub, e.g. `wallpaper-fleet-hub`.
2. Add an initial `config.json` at the repo root:
   ```json
   {
     "version": 0,
     "image_file": "wallpaper.jpg",
     "updated_at": "2026-08-01T00:00:00Z"
   }
   ```
3. Generate a **Personal Access Token**:
   - Fine-grained token scoped to just this repo, with **Contents: Read and write** permission, or
   - Classic token with the `repo` scope.
4. Edit `controller/config.py` and `client/config.py` so `GITHUB_OWNER` /
   `GITHUB_REPO` / `GITHUB_BRANCH` point at your repo (or set the
   `WFM_GITHUB_OWNER` / `WFM_GITHUB_REPO` / `WFM_GITHUB_BRANCH` env vars
   for the Controller).

## 2. Install dependencies

```
pip install -r requirements.txt
```

## 3. Running the Controller (on your admin machine)

```powershell
# PowerShell
$env:WFM_GITHUB_TOKEN = "ghp_xxxxxxxxxxxxxxxxxxxx"
python -m controller.main "C:\path\to\new_wallpaper.jpg" --message "Q3 branding refresh"
```

This uploads the image (fetching the file's SHA first, so the overwrite
is accepted) and bumps `version` in `config.json` (same SHA-first pattern).

## 4. Deploying the Client Agent on target Windows machines

Copy the whole `wallpaper-fleet-manager` folder to each target machine, e.g.:

```
C:\WallpaperFleetManager\wallpaper-fleet-manager\
```

You have two supported options for making it run **hidden, at startup,
with no visible console window**. Task Scheduler is recommended for
fleet deployment because it's scriptable and gives you more control
(run whether or not user is logged in, restart on failure, etc.).

### Option A — Task Scheduler (recommended)

1. Open **Task Scheduler** → **Create Task** (not "Create Basic Task", so you get the full options).
2. **General tab:**
   - Name: `Wallpaper Fleet Agent`
   - Select **"Run whether user is logged on or not"** (this is what fully suppresses any window, even more reliably than "Run only when logged on").
   - Check **"Run with highest privileges"** only if required by your environment (not needed for wallpaper changes, which are per-user).
   - Under "Configure for", pick your Windows version.
3. **Triggers tab:** → New → **"At log on"** (select "Any user" or a specific service account, per your fleet policy).
4. **Actions tab:** → New:
   - Action: **Start a program**
   - Program/script:
     ```
     C:\Users\<USERNAME>\AppData\Local\Programs\Python\Python312\pythonw.exe
     ```
   - Add arguments:
     ```
     -m client.main_agent
     ```
   - Start in (this is important — it must be the project root so the `client` package resolves):
     ```
     C:\WallpaperFleetManager\wallpaper-fleet-manager
     ```
5. **Conditions tab:** uncheck "Start the task only if the computer is on AC power" if these are laptops.
6. **Settings tab:** check **"If the task fails, restart every"** → 1 minute, and set "Attempt to restart up to" a high value, for resilience.
7. Click OK. If prompted, enter the credentials for the account the task runs as.

Using `pythonw.exe` (not `python.exe`) is what suppresses the console
window at the OS level — Task Scheduler alone does not need the `.vbs`
wrapper in this option.

### Option B — Startup folder + `.vbs` wrapper (simpler, per-user)

If you don't have Task Scheduler access (e.g. restricted environment), use
the included `run_agent_hidden.vbs`:

1. Edit `run_agent_hidden.vbs` and set the correct paths for `pythonwPath`
   and `scriptDir` on the target machine.
2. Press `Win + R`, type `shell:startup`, hit Enter — this opens the
   current user's Startup folder.
3. Place a **shortcut** to `run_agent_hidden.vbs` in that folder (not the
   file itself, a shortcut is fine and lets you set "Run: Minimized" as
   an extra precaution, though the VBScript's `objShell.Run ..., 0, False`
   already hides the window).

The `.vbs` wrapper's `0` flag is what guarantees zero visible window —
even a brief flash — because `WScript.Shell.Run` with window style `0`
never draws the console at all, unlike double-clicking a `.py`/`.bat`
file directly.

## 4. Verifying it's working

- Check `%LOCALAPPDATA%\WallpaperFleetManager\agent.log` on a client
  machine for entries like `Applied wallpaper version 3.`
- Check `%LOCALAPPDATA%\WallpaperFleetManager\version.txt` to see the
  currently-applied version number.
- If the wallpaper isn't updating, temporarily run
  `pythonw.exe -m client.main_agent` interactively by swapping in
  `python.exe` so you can see console output/tracebacks (only for
  debugging — never deploy with the visible console).

## Notes on resilience

`client/main_agent.py` wraps every polling cycle in a broad
`try/except Exception`. Any network failure, GitHub rate-limit, DNS
outage, malformed `config.json`, or Win32 API failure is logged to
`agent.log` and the loop simply waits `POLL_INTERVAL_SECONDS` (60s) and
tries again — the process itself never exits and never surfaces an
error dialog.
