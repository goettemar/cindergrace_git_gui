from git_ops import derive_repo_name


def test_derive_repo_name_basic():
    assert derive_repo_name("https://github.com/example/repo.git") == "repo"
    assert derive_repo_name("https://github.com/example/repo/") == "repo"
    assert derive_repo_name("repo") == "repo"
