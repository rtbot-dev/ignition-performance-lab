# Run the experiment from your terminal

The recommended entry point is the copy-and-paste terminal command in the root
README. It saves a versioned launcher as `ignition-lab.sh` (macOS/Linux) or
`ignition-lab.ps1` (Windows) in your current directory and runs it;
standard input remains available for the license question (no curl-to-shell pipe).
The macOS/Linux command uses the same portable shell launcher on both platforms.

The launchers download the versioned source bundle from this GitHub repository's
Releases, verify its SHA-256 against a value embedded in the launcher, and then
invoke the same shared startup scripts used when running from source.
They do not require Git, Python or manual ZIP extraction.

- **macOS:** open `Run-experiment-mac.command`. Requires Docker Desktop, curl and
  unzip. A downloaded script may require explicit approval in macOS security UI.
- **Windows:** open `Run-experiment-windows.cmd`. Requires Docker Desktop and
  Windows PowerShell 5.1+. Its embedded PowerShell is generated from the readable
  `.ps1` release asset. It uses a process-local execution-policy setting; it does
  not change machine policy. Managed-device policy can still block execution.
- **Linux:** run `sh Run-experiment-linux.sh`. Requires Docker Engine with Compose
  v2 (or Docker Desktop), curl and unzip. The user must already have Docker access;
  the launcher does not change permissions or invoke sudo. A desktop/browser is
  optional: the local lab URL is also printed.

All platforms ask for Ignition license acceptance on first launch. Docker must be
running. If the selected port is occupied by another Docker container, the launcher offers
three choices: stop the named container, use another port, or cancel. Stopping
requires an explicit selection and interrupts that container's service. For an
identified local process outside Docker, choose another port or stop it yourself.
The selected port is remembered in `runtime/port` and used for browser startup.
Set `LAB_PORT` to override it. Shell detection of non-Docker listeners uses `lsof`
when available; Docker may still report a conflict if another process binds later.
Downloads and image builds can take several minutes.

Install locations, separated by release:

- macOS/Linux: `${XDG_DATA_HOME:-$HOME/.local/share}/katenaria/ignition-performance-lab/<version>`.
- Windows: `%LOCALAPPDATA%/Katenaria/ignition-performance-lab/<version>`.

Within that directory, results are under `benchmarks/jython-vibration/results`.
Run `docker compose stop` from `benchmarks/jython-vibration` to stop the lab.
A repeated launch reuses the local package, credentials and gateway volume.
Different release directories still share the same Compose project identity;
stop the existing lab before changing release and use fresh state when comparing
independent cold-start tests.

The shell download/checksum/cache behavior is tested with controlled command
stubs. The Ignition project has been exercised on Apple Silicon with Docker
Desktop. Native Windows and Linux end-to-end execution remain unverified.
These are download-and-open launchers, not browser links that execute silently.

Build the source ZIP and launchers with `python3 scripts/build_release.py v0.1.3`.
The source archive excludes the generated launchers, avoiding a checksum cycle.

## Connect with Ignition Designer

After startup, the terminal prints the selected gateway URL, username `benchmark`,
the generated password and project `performance-lab`. Add that gateway in Designer
Launcher and sign in. The password is stored in the local benchmark `.env`; do not
share that file or unredacted terminal output. An existing gateway volume keeps its
original credentials, even if a different release generates a new `.env`. Reuse
the original credentials in that case; the launcher does not reset passwords.

## Latest release versus repeatable runs

The README uses GitHub's `/releases/latest/download/` URL. Running the full command
again downloads the current release's launcher. Each downloaded launcher still
pins its own release and package SHA-256, so it cannot accidentally combine files
from different versions. Running an already downloaded launcher reuses that version.
