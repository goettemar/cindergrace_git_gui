"""Commit message prompt builder."""

def build_commit_prompt(status_out: str, diff_text: str) -> str:
    status_trimmed = (status_out or "")[:2000]
    diff_trimmed = (diff_text or "")[:8000]
    return (
        "Generate a short git commit message (max 72 chars).\n"
        "Use imperative mood. No quotes. No trailing period.\n\n"
        f"Changed files:\n{status_trimmed}\n\n"
        f"Diff (truncated):\n{diff_trimmed}"
    )


__all__ = ["build_commit_prompt"]
