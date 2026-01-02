# Release Checklist

- [ ] Decide version and update `pyproject.toml`
- [ ] Run tests: `python3 -m pytest -q`
- [ ] Update README if needed
- [ ] Commit changes
- [ ] Tag release: `git tag vX.Y.Z`
- [ ] Push: `git push --tags`
- [ ] Build package: `python3 -m pip install build && python3 -m build`
- [ ] Create GitHub release and attach artifacts if desired
