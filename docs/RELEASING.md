# Create a downloadable release

The portable Windows archive lets users run the companion and flash the display without installing Python or PlatformIO. Git stores the source; generated firmware and executables are release assets, not committed binaries.

## GitHub

1. Push the reviewed, credential-free repository to your GitHub repository. Do not copy local configurations, logs or unrelated output files.
2. Ensure Actions is enabled. Set `FW_VERSION` to the intended version and pass CI. Commit before tagging.
3. Create and push a tag matching `FW_VERSION`, such as `v1.11.0`. This explicitly starts the Portable Windows release workflow.
4. The workflow builds/tests firmware on Linux, builds/tests the Windows executables and creates a **draft release** containing the Windows ZIP and its SHA-256 checksum. Drafts are invisible to ordinary downloaders.
5. Download the draft ZIP, extract it on Windows, test the menu, setup and firmware on the target board, and verify no private files are included. Review license notices and the corresponding upstream source.
6. Publish the reviewed draft using GitHub's Releases UI. README's recommended download is available after publication.

The workflow needs `contents: write` only in its draft-release job, uses GitHub's provided token, and contains no project API keys. A normal branch push runs CI but does not create a release. Failed or existing-tag releases must be resolved by the maintainer rather than silently replacing a published asset.

## Local build on Windows

Use Python 3.12 x64 and a clean checkout. Install host dependencies plus the pinned release tools in an isolated virtual environment:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1 -BuildTools
.\.venv\Scripts\python.exe -m pip install -r scripts/requirements-release.txt
.\.venv\Scripts\python.exe -m platformio run -e esp32p4-release
```

Copy the matching `fw_*.bin` and `fw_*.factory.bin` from that build into `work/prebuilt/application.bin` and `work/prebuilt/factory.bin`. Do not mix different builds. Then:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
.\.venv\Scripts\python.exe scripts/build_windows_release.py --firmware-dir work/prebuilt
```

The script builds `AI-Monitor.exe` and a separate upstream `firmware-flasher.exe`, exports tracked source, adds the matching images/manifest, gathers dependency licenses and esptool source, then creates the ZIP and internal file hashes in `work/windows-release`. It rejects an existing package directory so an old configuration cannot be silently mixed into a new release. Python/PlatformIO are needed only by the builder, not by the recipient of the portable ZIP.

Tagging/publishing is a maintainer action. Preparing an archive locally does not upload it to GitHub.
