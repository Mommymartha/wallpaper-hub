import os
import sys
import json
import tkinter as tk
from tkinter import simpledialog, messagebox

TOKEN_FILE = os.path.join(os.path.dirname(__file__), "local_config.json")

def load_github_token():
    # 1. Check local config file first
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r") as f:
                data = json.load(f)
                if data.get("token"):
                    return data["token"]
        except Exception:
            pass

    # 2. Check environment variable as fallback
    env_token = os.getenv("WFM_GITHUB_TOKEN", "")
    if env_token:
        return env_token

    # 3. Trigger a graphical modal prompt if no token exists (essential for .exe)
    root = tk.Tk()
    root.withdraw()  # Hide background root window
    token = simpledialog.askstring(
        "GitHub Authentication Required",
        "Enter your GitHub Personal Access Token (PAT):\n(This is required only on first launch)",
        show="*"
    )
    
    root.destroy()
    
    if not token or not token.strip():
        messagebox.showerror("Access Denied", "A valid GitHub Token is required to run the Wallpaper Fleet Controller.")
        sys.exit(1)

    clean_token = token.strip()
    try:
        with open(TOKEN_FILE, "w") as f:
            json.dump({"token": clean_token}, f)
        messagebox.showinfo("Setup Complete", "Token saved successfully. Launching controller...")
    except Exception as e:
        messagebox.showerror("Storage Error", f"Could not save local config: {e}")

    return clean_token


# --- FIXED EXPORTS ---
# These variable names now perfectly match what github_api.py and main.py are looking for.

GITHUB_OWNER = "Mommymartha"
GITHUB_REPO = "wallpaper-hub"
GITHUB_BRANCH = "main"

# Assign the dynamically loaded token to the correct variable name
GITHUB_TOKEN = load_github_token()

# Paths inside the GitHub repository
WALLPAPER_PATH_IN_REPO = "wallpaper.jpg"
CONFIG_JSON_PATH_IN_REPO = "config.json"

def contents_url(path_in_repo: str) -> str:
    """Returns the GitHub API URL for a specific file."""
    return f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{path_in_repo}"

def validate():
    """Ensure critical config exists before pushing."""
    if not GITHUB_TOKEN:
        raise EnvironmentError("GitHub token is missing.")