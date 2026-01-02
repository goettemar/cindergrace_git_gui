#!/usr/bin/env python3
"""Simple Git GUI using Tkinter."""
import json
import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Optional

from git_ops import (
    derive_repo_name,
    is_git_repo,
    read_git_config,
    run_git,
    ssh_key_status,
)
from openrouter import (
    CRYPTO_AVAILABLE,
    REQUESTS_AVAILABLE,
    InvalidToken,
    decrypt_api_key,
    encrypt_api_key,
    openrouter_request,
)
from prompt_builder import build_commit_prompt
from storage import load_list, load_profiles, save_list, save_profiles

FAVORITES_PATH = os.path.expanduser("~/.cindergrace_git_gui_favorites.json")
PROFILES_PATH = os.path.expanduser("~/.cindergrace_git_gui_profiles.json")
OPENROUTER_CONFIG_PATH = os.path.expanduser("~/.cindergrace_git_gui_openrouter.json")


class GitGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cindergrace Git GUI")
        self.geometry("1160x1080")
        self.resizable(True, True)

        self.repo_path = tk.StringVar()
        self.status_var = tk.StringVar(value="Select a git repository.")
        self.branch_var = tk.StringVar()
        self.remote_var = tk.StringVar(value="origin")
        self.remote_branch_var = tk.StringVar()
        self.clone_url_var = tk.StringVar()
        self.clone_dest_var = tk.StringVar()
        self.favorites_var = tk.StringVar()
        self.profile_var = tk.StringVar()
        self.profile_name_var = tk.StringVar()
        self.new_branch_var = tk.StringVar()
        self.commit_msg_var = tk.StringVar()
        self.openrouter_model_var = tk.StringVar(value="openai/gpt-4o-mini")
        self.openrouter_status_var = tk.StringVar(value="OpenRouter: not configured")
        self.output_queue = queue.Queue()
        self.busy = False
        self.favorites = self._load_favorites()
        self.profiles = self._load_profiles()
        self.openrouter_api_key: Optional[str] = None

        self._build_ui()
        self._poll_output()
        self._refresh_openrouter_status()

    def _build_ui(self):
        top_frame = ttk.Frame(self, padding=10)
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="Repository:").pack(side=tk.LEFT)
        repo_entry = ttk.Entry(top_frame, textvariable=self.repo_path, width=60)
        repo_entry.pack(side=tk.LEFT, padx=6, fill=tk.X, expand=True)
        ttk.Button(top_frame, text="Browse", command=self._browse_repo).pack(side=tk.LEFT)

        favorites_frame = ttk.Frame(self, padding=10)
        favorites_frame.pack(fill=tk.X)
        ttk.Label(favorites_frame, text="Favorites:").pack(side=tk.LEFT)
        self.favorites_combo = ttk.Combobox(
            favorites_frame,
            textvariable=self.favorites_var,
            values=self.favorites,
            state="readonly",
        )
        self.favorites_combo.pack(side=tk.LEFT, padx=6, fill=tk.X, expand=True)
        self.load_fav_btn = ttk.Button(favorites_frame, text="Load", command=self._load_favorite)
        self.add_fav_btn = ttk.Button(favorites_frame, text="Add Current", command=self._add_favorite)
        self.remove_fav_btn = ttk.Button(favorites_frame, text="Remove", command=self._remove_favorite)
        self.load_fav_btn.pack(side=tk.LEFT, padx=4)
        self.add_fav_btn.pack(side=tk.LEFT, padx=4)
        self.remove_fav_btn.pack(side=tk.LEFT, padx=4)

        profile_frame = ttk.Frame(self, padding=10)
        profile_frame.pack(fill=tk.X)
        ttk.Label(profile_frame, text="Profiles:").pack(side=tk.LEFT)
        self.profile_combo = ttk.Combobox(
            profile_frame,
            textvariable=self.profile_var,
            values=sorted(self.profiles.keys()),
            state="readonly",
        )
        self.profile_combo.pack(side=tk.LEFT, padx=6, fill=tk.X, expand=True)
        self.profile_load_btn = ttk.Button(profile_frame, text="Load", command=self._load_profile)
        self.profile_delete_btn = ttk.Button(profile_frame, text="Delete", command=self._delete_profile)
        self.profile_load_btn.pack(side=tk.LEFT, padx=4)
        self.profile_delete_btn.pack(side=tk.LEFT, padx=4)

        profile_save_frame = ttk.Frame(self, padding=10)
        profile_save_frame.pack(fill=tk.X)
        ttk.Label(profile_save_frame, text="Profile Name:").pack(side=tk.LEFT)
        ttk.Entry(profile_save_frame, textvariable=self.profile_name_var, width=30).pack(side=tk.LEFT, padx=6)
        self.profile_save_btn = ttk.Button(profile_save_frame, text="Save/Update", command=self._save_profile)
        self.profile_save_btn.pack(side=tk.LEFT, padx=4)

        action_frame = ttk.Frame(self, padding=10)
        action_frame.pack(fill=tk.X)

        self.status_btn = ttk.Button(action_frame, text="Status", command=self._status)
        self.pull_btn = ttk.Button(action_frame, text="Pull", command=self._pull)
        self.push_btn = ttk.Button(action_frame, text="Push", command=self._push)
        self.log_btn = ttk.Button(action_frame, text="Log", command=self._log)
        self.fetch_btn = ttk.Button(action_frame, text="Fetch", command=self._fetch)
        self.rebase_btn = ttk.Button(action_frame, text="Rebase", command=self._rebase)
        self.stash_btn = ttk.Button(action_frame, text="Stash", command=self._stash)
        self.stash_pop_btn = ttk.Button(action_frame, text="Stash Pop", command=self._stash_pop)
        self.branches_btn = ttk.Button(action_frame, text="Refresh Branches", command=self._refresh_branches)
        self.checkout_btn = ttk.Button(action_frame, text="Checkout", command=self._checkout_branch)
        self.auth_btn = ttk.Button(action_frame, text="Auth Check", command=self._auth_check)

        for btn in [
            self.status_btn,
            self.pull_btn,
            self.push_btn,
            self.log_btn,
            self.fetch_btn,
            self.rebase_btn,
            self.stash_btn,
            self.stash_pop_btn,
            self.branches_btn,
            self.checkout_btn,
            self.auth_btn,
        ]:
            btn.pack(side=tk.LEFT, padx=4)

        branch_frame = ttk.Frame(self, padding=10)
        branch_frame.pack(fill=tk.X)
        ttk.Label(branch_frame, text="Branch:").pack(side=tk.LEFT)
        self.branch_combo = ttk.Combobox(branch_frame, textvariable=self.branch_var, values=[], state="readonly")
        self.branch_combo.pack(side=tk.LEFT, padx=6, fill=tk.X, expand=True)
        ttk.Label(branch_frame, text="Remote:").pack(side=tk.LEFT, padx=6)
        ttk.Entry(branch_frame, textvariable=self.remote_var, width=12).pack(side=tk.LEFT)

        remote_frame = ttk.Frame(self, padding=10)
        remote_frame.pack(fill=tk.X)
        ttk.Label(remote_frame, text="Remote Branch:").pack(side=tk.LEFT)
        self.remote_combo = ttk.Combobox(
            remote_frame,
            textvariable=self.remote_branch_var,
            values=[],
            state="readonly",
        )
        self.remote_combo.pack(side=tk.LEFT, padx=6, fill=tk.X, expand=True)
        self.checkout_remote_btn = ttk.Button(
            remote_frame,
            text="Checkout Remote",
            command=self._checkout_remote_branch,
        )
        self.checkout_remote_btn.pack(side=tk.LEFT, padx=4)

        branch_manage_frame = ttk.Frame(self, padding=10)
        branch_manage_frame.pack(fill=tk.X)
        ttk.Label(branch_manage_frame, text="New Branch:").pack(side=tk.LEFT)
        ttk.Entry(branch_manage_frame, textvariable=self.new_branch_var, width=30).pack(side=tk.LEFT, padx=6)
        self.create_branch_btn = ttk.Button(branch_manage_frame, text="Create", command=self._create_branch)
        self.delete_branch_btn = ttk.Button(branch_manage_frame, text="Delete", command=self._delete_branch)
        self.create_branch_btn.pack(side=tk.LEFT, padx=4)
        self.delete_branch_btn.pack(side=tk.LEFT, padx=4)

        commit_frame = ttk.Frame(self, padding=10)
        commit_frame.pack(fill=tk.X)
        ttk.Label(commit_frame, text="Commit Message:").pack(side=tk.LEFT)
        ttk.Entry(commit_frame, textvariable=self.commit_msg_var, width=50).pack(side=tk.LEFT, padx=6, fill=tk.X, expand=True)
        self.stage_btn = ttk.Button(commit_frame, text="Stage All", command=self._stage_all)
        self.commit_btn = ttk.Button(commit_frame, text="Commit", command=self._commit)
        self.stage_btn.pack(side=tk.LEFT, padx=4)
        self.commit_btn.pack(side=tk.LEFT, padx=4)

        openrouter_frame = ttk.LabelFrame(self, text="OpenRouter Commit Helper", padding=10)
        openrouter_frame.pack(fill=tk.X, padx=10, pady=6)
        ttk.Label(openrouter_frame, text="Model:").grid(row=0, column=0, sticky="w")
        ttk.Entry(openrouter_frame, textvariable=self.openrouter_model_var, width=40).grid(
            row=0, column=1, sticky="w", padx=6
        )
        self.openrouter_status_label = ttk.Label(openrouter_frame, textvariable=self.openrouter_status_var)
        self.openrouter_status_label.grid(row=0, column=2, sticky="w", padx=6)

        self.openrouter_set_btn = ttk.Button(openrouter_frame, text="Set API Key", command=self._set_openrouter_key)
        self.openrouter_unlock_btn = ttk.Button(openrouter_frame, text="Unlock Key", command=self._unlock_openrouter_key)
        self.openrouter_test_btn = ttk.Button(openrouter_frame, text="Test", command=self._test_openrouter)
        self.openrouter_suggest_btn = ttk.Button(
            openrouter_frame,
            text="Suggest Commit Message",
            command=self._suggest_commit_message,
        )
        self.openrouter_set_btn.grid(row=1, column=0, pady=4, sticky="w")
        self.openrouter_unlock_btn.grid(row=1, column=1, pady=4, sticky="w")
        self.openrouter_test_btn.grid(row=1, column=2, pady=4, sticky="w")
        self.openrouter_suggest_btn.grid(row=1, column=3, pady=4, sticky="w")
        openrouter_frame.columnconfigure(3, weight=1)

        clone_frame = ttk.Frame(self, padding=10)
        clone_frame.pack(fill=tk.X)
        ttk.Label(clone_frame, text="Clone URL:").grid(row=0, column=0, sticky="w")
        ttk.Entry(clone_frame, textvariable=self.clone_url_var, width=60).grid(
            row=0, column=1, padx=6, sticky="ew"
        )
        ttk.Label(clone_frame, text="Destination:").grid(row=1, column=0, sticky="w")
        ttk.Entry(clone_frame, textvariable=self.clone_dest_var, width=60).grid(
            row=1, column=1, padx=6, sticky="ew"
        )
        ttk.Button(clone_frame, text="Browse", command=self._browse_clone_dest).grid(
            row=1, column=2, padx=4
        )
        self.clone_btn = ttk.Button(clone_frame, text="Clone", command=self._clone_repo)
        self.clone_btn.grid(row=0, column=2, padx=4)
        clone_frame.columnconfigure(1, weight=1)

        status_frame = ttk.Frame(self, padding=10)
        status_frame.pack(fill=tk.X)
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT)

        output_frame = ttk.Frame(self, padding=10)
        output_frame.pack(fill=tk.BOTH, expand=True)

        self.output_text = tk.Text(output_frame, wrap=tk.WORD, height=12)
        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(output_frame, command=self.output_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.output_text.configure(yscrollcommand=scrollbar.set)

        history_frame = ttk.Frame(self, padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True)
        history_header = ttk.Frame(history_frame)
        history_header.pack(fill=tk.X)
        ttk.Label(history_header, text="History (last 50 commits)").pack(side=tk.LEFT)
        self.refresh_history_btn = ttk.Button(history_header, text="Refresh History", command=self._refresh_history)
        self.refresh_history_btn.pack(side=tk.LEFT, padx=6)
        self.history_text = tk.Text(history_frame, wrap=tk.WORD, height=10)
        self.history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        history_scroll = ttk.Scrollbar(history_frame, command=self.history_text.yview)
        history_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_text.configure(yscrollcommand=history_scroll.set)

        diff_frame = ttk.Frame(self, padding=10)
        diff_frame.pack(fill=tk.BOTH, expand=True)
        diff_header = ttk.Frame(diff_frame)
        diff_header.pack(fill=tk.X)
        ttk.Label(diff_header, text="Diff Summary").pack(side=tk.LEFT)
        self.refresh_diff_btn = ttk.Button(diff_header, text="Refresh Diff", command=self._refresh_diff)
        self.refresh_diff_btn.pack(side=tk.LEFT, padx=6)
        self.diff_text = tk.Text(diff_frame, wrap=tk.WORD, height=10)
        self.diff_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        diff_scroll = ttk.Scrollbar(diff_frame, command=self.diff_text.yview)
        diff_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.diff_text.configure(yscrollcommand=diff_scroll.set)

        note_frame = ttk.Frame(self, padding=10)
        note_frame.pack(fill=tk.X)
        ttk.Label(
            note_frame,
            text=(
                "Note: If git asks for credentials, configure a credential helper or use terminal auth."
            ),
        ).pack(side=tk.LEFT)

    def _set_busy(self, busy, message=None):
        self.busy = busy
        for btn in [
            self.status_btn,
            self.pull_btn,
            self.push_btn,
            self.log_btn,
            self.fetch_btn,
            self.rebase_btn,
            self.stash_btn,
            self.stash_pop_btn,
            self.branches_btn,
            self.checkout_btn,
            self.checkout_remote_btn,
            self.create_branch_btn,
            self.delete_branch_btn,
            self.stage_btn,
            self.commit_btn,
            self.clone_btn,
            self.load_fav_btn,
            self.add_fav_btn,
            self.remove_fav_btn,
            self.profile_load_btn,
            self.profile_delete_btn,
            self.profile_save_btn,
            self.auth_btn,
            self.refresh_history_btn,
            self.refresh_diff_btn,
            self.openrouter_set_btn,
            self.openrouter_unlock_btn,
            self.openrouter_test_btn,
            self.openrouter_suggest_btn,
        ]:
            btn.configure(state=(tk.DISABLED if busy else tk.NORMAL))
        if message is not None:
            self.status_var.set(message)

    def _append_output(self, text):
        self.output_text.insert(tk.END, text + "\n")
        self.output_text.see(tk.END)

    def _set_history(self, text):
        self.history_text.delete("1.0", tk.END)
        self.history_text.insert(tk.END, text)

    def _set_diff(self, text):
        self.diff_text.delete("1.0", tk.END)
        self.diff_text.insert(tk.END, text)

    def _browse_repo(self):
        path = filedialog.askdirectory()
        if path:
            self._set_repo_path(path)

    def _browse_clone_dest(self):
        path = filedialog.askdirectory()
        if path:
            self.clone_dest_var.set(path)

    def _set_repo_path(self, path):
        self.repo_path.set(path)
        self._append_output(f"Selected repo: {path}")
        self._refresh_branches()
        self._refresh_history()
        self._refresh_diff()

    def _ensure_repo(self):
        path = self.repo_path.get().strip()
        if not path:
            messagebox.showerror("Missing repo", "Please select a repository.")
            return None
        if not os.path.isdir(path):
            messagebox.showerror("Invalid repo", "Path does not exist.")
            return None
        if not is_git_repo(path):
            messagebox.showerror("Invalid repo", "Selected folder is not a git repository.")
            return None
        return path

    def _run_async(self, args, description):
        repo = self._ensure_repo()
        if not repo:
            return
        self._run_async_with_cwd(args, repo, description)

    def _run_async_with_cwd(self, args, cwd, description):
        if self.busy:
            return
        self._set_busy(True, f"Running: git {' '.join(args)}")

        def worker():
            code, out, err = run_git(args, cwd)
            self.output_queue.put((description, args, code, out, err))

        threading.Thread(target=worker, daemon=True).start()

    def _poll_output(self):
        try:
            while True:
                description, args, code, out, err = self.output_queue.get_nowait()
                self._append_output(f"$ git {' '.join(args)}")
                if out:
                    self._append_output(out)
                if err:
                    self._append_output(err)
                self._append_output(f"Exit code: {code}\n")
                self._set_busy(False, f"Done: {description}")
        except queue.Empty:
            pass
        self.after(200, self._poll_output)

    def _status(self):
        self._run_async(["status"], "status")

    def _pull(self):
        if not messagebox.askyesno("Confirm", "Run git pull?"):
            return
        self._run_async(["pull"], "pull")

    def _push(self):
        if not messagebox.askyesno("Confirm", "Run git push?"):
            return
        self._run_async(["push"], "push")

    def _log(self):
        self._run_async(["log", "--oneline", "-20"], "log")

    def _fetch(self):
        if not messagebox.askyesno("Confirm", "Run git fetch?"):
            return
        self._run_async(["fetch", "--all", "--prune"], "fetch")

    def _rebase(self):
        if not messagebox.askyesno("Confirm", "Run git rebase onto <remote>/<branch>?"):
            return
        repo = self._ensure_repo()
        if not repo:
            return
        branch = self.branch_var.get().strip()
        if not branch:
            messagebox.showerror("Missing branch", "Please select a branch.")
            return
        remote = self.remote_var.get().strip() or "origin"
        self._run_async_with_cwd(["rebase", f"{remote}/{branch}"], repo, f"rebase {branch}")

    def _stash(self):
        if not messagebox.askyesno("Confirm", "Stash changes? (git stash push)"):
            return
        self._run_async(["stash", "push"], "stash push")

    def _stash_pop(self):
        if not messagebox.askyesno("Confirm", "Pop latest stash? (git stash pop)"):
            return
        self._run_async(["stash", "pop"], "stash pop")

    def _stage_all(self):
        if not messagebox.askyesno("Confirm", "Stage all changes? (git add -A)"):
            return
        self._run_async(["add", "-A"], "stage all")

    def _commit(self):
        msg = self.commit_msg_var.get().strip()
        if not msg:
            messagebox.showerror("Missing message", "Please enter a commit message.")
            return
        if not messagebox.askyesno("Confirm", f"Commit with message:\n{msg}"):
            return
        self._run_async(["commit", "-m", msg], "commit")

    def _refresh_history(self):
        repo = self._ensure_repo()
        if not repo:
            return
        code, out, err = run_git(["log", "--oneline", "-50"], repo)
        if code != 0:
            self._set_history(err or "Failed to read history.")
            return
        self._set_history(out or "No commits found.")

    def _refresh_diff(self):
        repo = self._ensure_repo()
        if not repo:
            return
        code, status_out, status_err = run_git(["status", "-s"], repo)
        code_diff, diff_out, diff_err = run_git(["diff", "--stat"], repo)
        if code != 0:
            self._set_diff(status_err or "Failed to read status.")
            return
        if code_diff != 0:
            self._set_diff(diff_err or "Failed to read diff.")
            return
        parts = []
        if status_out:
            parts.append("Changed files:\n" + status_out)
        else:
            parts.append("Changed files: none")
        if diff_out:
            parts.append("\nDiff summary:\n" + diff_out)
        else:
            parts.append("\nDiff summary: clean")
        self._set_diff("\n".join(parts))

    def _refresh_branches(self):
        repo = self._ensure_repo()
        if not repo:
            return
        code, out, err = run_git(["branch"], repo)
        if code != 0:
            messagebox.showerror("Error", err or "Failed to list branches.")
            return
        branches = []
        current = ""
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("*"):
                current = line[1:].strip()
                branches.append(current)
            elif line:
                branches.append(line)
        self.branch_combo["values"] = branches
        if current:
            self.branch_var.set(current)

        remote_code, remote_out, remote_err = run_git(["branch", "-a"], repo)
        if remote_code != 0:
            messagebox.showerror("Error", remote_err or "Failed to list remote branches.")
            return
        remote_branches = []
        for line in remote_out.splitlines():
            entry = line.strip()
            if entry.startswith("*"):
                entry = entry[1:].strip()
            if "->" in entry:
                continue
            if entry.startswith("remotes/"):
                entry = entry.replace("remotes/", "", 1)
            if entry and "/" in entry:
                remote_branches.append(entry)
        remote_branches = sorted(set(remote_branches))
        self.remote_combo["values"] = remote_branches
        if remote_branches:
            if self.remote_branch_var.get() not in remote_branches:
                self.remote_branch_var.set(remote_branches[0])

        self.status_var.set("Branches refreshed.")

    def _checkout_branch(self):
        branch = self.branch_var.get().strip()
        if not branch:
            messagebox.showerror("Missing branch", "Please select a branch.")
            return
        if not messagebox.askyesno("Confirm", f"Checkout branch '{branch}'?"):
            return
        self._run_async(["checkout", branch], f"checkout {branch}")

    def _checkout_remote_branch(self):
        remote_branch = self.remote_branch_var.get().strip()
        if not remote_branch:
            messagebox.showerror("Missing branch", "Please select a remote branch.")
            return
        local_branch = remote_branch.split("/", 1)[-1]
        if not messagebox.askyesno(
            "Confirm",
            f"Checkout remote '{remote_branch}' as local '{local_branch}'?",
        ):
            return
        self._run_async(["checkout", "-b", local_branch, remote_branch], f"checkout {remote_branch}")

    def _create_branch(self):
        name = self.new_branch_var.get().strip()
        if not name:
            messagebox.showerror("Missing name", "Please enter a new branch name.")
            return
        if not messagebox.askyesno("Confirm", f"Create branch '{name}'?"):
            return
        self._run_async(["checkout", "-b", name], f"create branch {name}")

    def _delete_branch(self):
        name = self.branch_var.get().strip()
        if not name:
            messagebox.showerror("Missing branch", "Please select a branch to delete.")
            return
        if not messagebox.askyesno("Confirm", f"Delete branch '{name}'? (git branch -D)"):
            return
        self._run_async(["branch", "-D", name], f"delete branch {name}")

    def _load_favorites(self):
        return load_list(FAVORITES_PATH)

    def _save_favorites(self):
        try:
            save_list(FAVORITES_PATH, self.favorites)
        except OSError as exc:
            messagebox.showerror("Error", f"Failed to save favorites: {exc}")

    def _refresh_favorites_combo(self):
        self.favorites_combo["values"] = self.favorites
        if self.favorites:
            if self.favorites_var.get() not in self.favorites:
                self.favorites_var.set(self.favorites[0])
        else:
            self.favorites_var.set("")

    def _load_favorite(self):
        path = self.favorites_var.get().strip()
        if not path:
            messagebox.showerror("Missing favorite", "Please select a favorite.")
            return
        self._set_repo_path(path)

    def _add_favorite(self):
        path = self.repo_path.get().strip()
        if not path:
            messagebox.showerror("Missing repo", "Please select a repository.")
            return
        if not os.path.isdir(path):
            messagebox.showerror("Invalid path", "Path does not exist.")
            return
        if path not in self.favorites:
            self.favorites.append(path)
            self._save_favorites()
            self._refresh_favorites_combo()
            self.status_var.set("Favorite added.")

    def _remove_favorite(self):
        path = self.favorites_var.get().strip()
        if not path:
            messagebox.showerror("Missing favorite", "Please select a favorite.")
            return
        if path in self.favorites:
            self.favorites.remove(path)
            self._save_favorites()
            self._refresh_favorites_combo()
            self.status_var.set("Favorite removed.")

    def _load_profiles(self):
        return load_profiles(PROFILES_PATH)

    def _save_profiles(self):
        try:
            save_profiles(PROFILES_PATH, self.profiles)
        except OSError as exc:
            messagebox.showerror("Error", f"Failed to save profiles: {exc}")

    def _refresh_profiles_combo(self):
        self.profile_combo["values"] = sorted(self.profiles.keys())
        if self.profile_var.get() not in self.profiles:
            self.profile_var.set("")

    def _load_profile(self):
        name = self.profile_var.get().strip()
        if not name:
            messagebox.showerror("Missing profile", "Please select a profile.")
            return
        profile = self.profiles.get(name)
        if not profile:
            messagebox.showerror("Missing profile", "Profile not found.")
            return
        path = profile.get("path", "")
        remote = profile.get("remote", "origin")
        branch = profile.get("branch", "")
        if path:
            self._set_repo_path(path)
        self.remote_var.set(remote or "origin")
        if branch:
            self.branch_var.set(branch)
        self.profile_name_var.set(name)
        self.status_var.set(f"Profile loaded: {name}")

    def _save_profile(self):
        name = self.profile_name_var.get().strip() or self.profile_var.get().strip()
        if not name:
            messagebox.showerror("Missing name", "Please enter a profile name.")
            return
        repo = self._ensure_repo()
        if not repo:
            return
        profile = {
            "path": repo,
            "remote": self.remote_var.get().strip() or "origin",
            "branch": self.branch_var.get().strip(),
        }
        self.profiles[name] = profile
        self._save_profiles()
        self._refresh_profiles_combo()
        self.profile_var.set(name)
        self.status_var.set(f"Profile saved: {name}")

    def _delete_profile(self):
        name = self.profile_var.get().strip()
        if not name:
            messagebox.showerror("Missing profile", "Please select a profile.")
            return
        if not messagebox.askyesno("Confirm", f"Delete profile '{name}'?"):
            return
        if name in self.profiles:
            del self.profiles[name]
            self._save_profiles()
            self._refresh_profiles_combo()
            self.status_var.set("Profile deleted.")

    def _auth_check(self):
        name = read_git_config("user.name")
        email = read_git_config("user.email")
        helper = read_git_config("credential.helper")
        keys = ssh_key_status()

        lines = ["Auth check:", f"- user.name: {name or 'missing'}", f"- user.email: {email or 'missing'}"]
        lines.append(f"- credential.helper: {helper or 'not set'}")
        if keys:
            lines.append("- ssh keys: " + ", ".join(keys))
        else:
            lines.append("- ssh keys: none found (~/.ssh/id_ed25519 or id_rsa)")

        self._append_output("\n".join(lines))

    def _clone_repo(self):
        url = self.clone_url_var.get().strip()
        dest_input = self.clone_dest_var.get().strip()
        if not url:
            messagebox.showerror("Missing URL", "Please enter a clone URL.")
            return
        if not dest_input:
            messagebox.showerror("Missing destination", "Please choose a destination folder.")
            return

        if os.path.isdir(dest_input):
            target = os.path.join(dest_input, derive_repo_name(url))
        else:
            target = dest_input
        parent = os.path.dirname(os.path.abspath(target))
        if not os.path.isdir(parent):
            messagebox.showerror("Invalid destination", "Destination parent folder does not exist.")
            return
        if os.path.exists(target):
            messagebox.showerror("Invalid destination", "Destination already exists.")
            return

        if not messagebox.askyesno("Confirm", f"Clone into {target}?"):
            return
        self._run_async_with_cwd(["clone", url, target], parent, "clone repo")

    def _refresh_openrouter_status(self):
        if not CRYPTO_AVAILABLE:
            self.openrouter_status_var.set("OpenRouter: cryptography not installed")
            return
        if not REQUESTS_AVAILABLE:
            self.openrouter_status_var.set("OpenRouter: requests not installed")
            return
        if not os.path.exists(OPENROUTER_CONFIG_PATH):
            self.openrouter_status_var.set("OpenRouter: no key saved")
            return
        if self.openrouter_api_key:
            self.openrouter_status_var.set("OpenRouter: unlocked")
        else:
            self.openrouter_status_var.set("OpenRouter: locked")

    def _set_openrouter_key(self):
        if not CRYPTO_AVAILABLE:
            messagebox.showerror("Missing dependency", "Install cryptography to store the key securely.")
            return
        api_key = simpledialog.askstring("OpenRouter", "Enter OpenRouter API key:", show="*")
        if not api_key:
            return
        password = simpledialog.askstring("OpenRouter", "Set a password to encrypt the key:", show="*")
        if not password:
            return
        payload = encrypt_api_key(api_key.strip(), password)
        try:
            with open(OPENROUTER_CONFIG_PATH, "w", encoding="utf-8") as handle:
                json.dump(payload, handle)
            self.openrouter_api_key = api_key.strip()
            self._refresh_openrouter_status()
            self._append_output("OpenRouter key saved and unlocked.")
        except OSError as exc:
            messagebox.showerror("Error", f"Failed to save key: {exc}")

    def _unlock_openrouter_key(self):
        if not CRYPTO_AVAILABLE:
            messagebox.showerror("Missing dependency", "Install cryptography to unlock the key.")
            return
        if not os.path.exists(OPENROUTER_CONFIG_PATH):
            messagebox.showerror("Missing key", "No encrypted key found.")
            return
        password = simpledialog.askstring("OpenRouter", "Enter password:", show="*")
        if not password:
            return
        try:
            with open(OPENROUTER_CONFIG_PATH, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.openrouter_api_key = decrypt_api_key(payload, password)
            self._refresh_openrouter_status()
            self._append_output("OpenRouter key unlocked for this session.")
        except InvalidToken:
            messagebox.showerror("Error", "Invalid password.")
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            messagebox.showerror("Error", f"Failed to unlock key: {exc}")

    def _test_openrouter(self):
        if not REQUESTS_AVAILABLE:
            messagebox.showerror("Missing dependency", "Install requests to use OpenRouter.")
            return
        if not self.openrouter_api_key:
            messagebox.showerror("OpenRouter", "Unlock or set the API key first.")
            return
        model = self.openrouter_model_var.get().strip() or "openai/gpt-4o-mini"
        prompt = "Reply with the word OK."
        try:
            result = openrouter_request(self.openrouter_api_key, model, prompt)
            self._append_output(f"OpenRouter test response: {result}")
        except RuntimeError as exc:
            messagebox.showerror("OpenRouter", str(exc))

    def _collect_commit_context(self, repo: str) -> str:
        _, status_out, _ = run_git(["status", "-s"], repo)
        _, diff_cached, _ = run_git(["diff", "--cached"], repo)
        _, diff_working, _ = run_git(["diff"], repo)
        diff_text = diff_cached or diff_working
        return build_commit_prompt(status_out, diff_text)

    def _suggest_commit_message(self):
        if not REQUESTS_AVAILABLE:
            messagebox.showerror("Missing dependency", "Install requests to use OpenRouter.")
            return
        if not self.openrouter_api_key:
            messagebox.showerror("OpenRouter", "Unlock or set the API key first.")
            return
        repo = self._ensure_repo()
        if not repo:
            return
        model = self.openrouter_model_var.get().strip() or "openai/gpt-4o-mini"
        prompt = self._collect_commit_context(repo)
        self._set_busy(True, "Generating commit message...")

        def worker():
            try:
                suggestion = openrouter_request(self.openrouter_api_key, model, prompt)
                self.output_queue.put(("openrouter", ["openrouter"], 0, suggestion, ""))
                self.commit_msg_var.set(suggestion.strip())
            except Exception as exc:
                self.output_queue.put(("openrouter", ["openrouter"], 1, "", str(exc)))

        threading.Thread(target=worker, daemon=True).start()


def main() -> None:
    app = GitGui()
    app.mainloop()


if __name__ == "__main__":
    main()
