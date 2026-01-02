from prompt_builder import build_commit_prompt


def test_build_commit_prompt_trims():
    status = "x" * 3000
    diff = "y" * 9000
    prompt = build_commit_prompt(status, diff)
    assert "Changed files" in prompt
    assert "Diff (truncated)" in prompt
    assert len(prompt) < 12000
