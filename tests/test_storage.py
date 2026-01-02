from storage import load_list, load_profiles, save_list, save_profiles


def test_save_and_load_list(tmp_path):
    path = tmp_path / "favorites.json"
    save_list(str(path), ["a", "b", "a", 1])
    assert load_list(str(path)) == ["a", "b"]


def test_save_and_load_profiles(tmp_path):
    path = tmp_path / "profiles.json"
    data = {"main": {"path": "/tmp/repo", "remote": "origin", "branch": "main"}}
    save_profiles(str(path), data)
    assert load_profiles(str(path)) == data
