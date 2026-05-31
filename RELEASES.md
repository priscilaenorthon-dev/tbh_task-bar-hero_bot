# Releases & builds

How to build **TBH Helper** locally and publish GitHub releases.

Workflow file: [.github/workflows/release.yml](.github/workflows/release.yml)

---

## Local build (on your PC)

Requirements: Windows, Python 3.10+

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --name TBHHelper --add-data "resources;resources" --add-data "assets;assets" main.py
```

Output:

- Folder: `dist/TBHHelper/`
- Executable: `dist/TBHHelper/TBHHelper.exe`

The folder includes bundled `resources/` and `assets/`. Zip the whole `TBHHelper` folder if you want to share it manually.

Do **not** commit `dist/`, `build/`, or `.exe` files to git.

---

## Automated releases (GitHub Actions)

The **Release** workflow runs when you push a version tag (`v*`, e.g. `v1.0.0`).

It builds the Windows executable, zips `dist/TBHHelper/`, and creates a GitHub Release with **TBHHelper-Windows.zip** attached.

```bash
git checkout main
git pull
git tag v1.0.0
git push origin v1.0.0
```

Replace `v1.0.0` with your actual version each time. Open **Releases** on GitHub to download the zip.

### Release checklist

- [ ] Changes pushed to `main`
- [ ] Tag name starts with `v` (e.g. `v1.0.0`)
- [ ] **Release** workflow finished successfully
- [ ] **TBHHelper-Windows.zip** appears on the release page
- [ ] Smoke-test: unzip and run `TBHHelper.exe` on Windows

---

## Troubleshooting

| Problem | What to try |
|--------|-------------|
| Release has no zip | Tag must be `v*` (e.g. `v1.0.0`), not `1.0.0` |
| Workflow did not run | Confirm the tag was pushed: `git push origin v1.0.0` |
| Exe won't start | Run from the unzipped `TBHHelper` folder (not only the `.exe` moved alone) |

---

## Quick reference

| Goal | Command / action |
|------|------------------|
| Run from source | `python main.py` |
| Build locally | `pyinstaller --name TBHHelper --add-data "resources;resources" --add-data "assets;assets" main.py` |
| New release | `git tag v1.0.0 && git push origin v1.0.0` |
