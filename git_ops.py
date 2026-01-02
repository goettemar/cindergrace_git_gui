"""Git command helpers."""

import os
import subprocess


def run_git(args, cwd):
    """Run a git command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return 127, "", "git not found in PATH"


def is_git_repo(path):
    code, out, _ = run_git(["rev-parse", "--is-inside-work-tree"], path)
    return code == 0 and out.strip() == "true"


def derive_repo_name(url):
    base = url.rstrip("/").split("/")[-1]
    if base.endswith(".git"):
        base = base[:-4]
    return base or "repo"


def read_git_config(key):
    code, out, _ = run_git(["config", "--global", key], os.getcwd())
    if code != 0:
        return ""
    return out.strip()


def ssh_key_status():
    candidates = [
        os.path.expanduser("~/.ssh/id_ed25519"),
        os.path.expanduser("~/.ssh/id_rsa"),
    ]
    return [path for path in candidates if os.path.exists(path)]


__all__ = [
    "run_git",
    "is_git_repo",
    "derive_repo_name",
    "read_git_config",
    "ssh_key_status",
]
