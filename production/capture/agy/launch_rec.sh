#!/usr/bin/env bash
# Launch a recording-only Antigravity instance, fully isolated from the user's own Antigravity:
#   - separate Electron profile (--user-data-dir)
#   - separate HOME (Antigravity keeps conversations/skills/settings under ~/.gemini/…), so the user's
#     projects and history never appear on camera
#   - CDP on :9333 so captures use the same screencast pipeline as the GE recordings
#   - auto-updater host blocked: an available update made the app shut down its language server
#     and drop the window mid-recording
# Usage: production/capture/agy/launch_rec.sh [fresh]   ("fresh" wipes the recording HOME first)
set -euo pipefail
REC="$HOME/agy-rec"
if [[ "${1:-}" == "fresh" ]]; then
  rm -rf "$REC"
fi
mkdir -p "$REC/home" "$REC/profile" "$REC/work"
# keep the real HOME's Xcode/CLT/git config available for builds inside demos
[[ -f "$HOME/.gitconfig" && ! -e "$REC/home/.gitconfig" ]] && cp "$HOME/.gitconfig" "$REC/home/.gitconfig"
if pgrep -f "remote-debugging-port=9333" >/dev/null; then
  echo "recording instance already running"; exit 0
fi
# start in a NEW SESSION: otherwise whoever ran this script (terminal/agent task) kills the process group on exit,
# which SIGTERMs the language server and the window disappears.
HOME="$REC/home" CFFIXED_USER_HOME="$REC/home" REC="$REC" python3 - <<'PY'
import os, subprocess
rec = os.environ["REC"]
log = open(f"{rec}/antigravity.log", "ab")
# (optional) block the auto-updater host for the session: an update mid-take shuts the language server down —
# set AG_BLOCK_UPDATER_HOST to the updater host name your build uses.
args = ["/Applications/Antigravity.app/Contents/MacOS/Antigravity",
        f"--user-data-dir={rec}/profile", "--remote-debugging-port=9333"]
if os.environ.get("AG_BLOCK_UPDATER_HOST"):
    args.append(f"--host-resolver-rules=MAP {os.environ['AG_BLOCK_UPDATER_HOST']} ~NOTFOUND")
p = subprocess.Popen(args,
                     stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
print("started pid", p.pid)
PY
