#!/usr/bin/env bash
# Recording-only Antigravity instance for the AG "cymbal-voc" storyline (Labs 3–10), isolated from your own Antigravity:
#   - HOME isolated ($REC/home): only account/install ids are copied from ~/.gemini (no conversation history)
#   - Electron profile copied without caches/backups/workspace storage (auth lives in User/globalStorage + keychain)
#   - gcloud config copied into the isolated HOME (project $LAB_PROJECT_ID) and ADC = the freshly logged-in gcloud account
#     with quota project $LAB_PROJECT_ID → MCP servers with "authProviderType": "google_credentials" (BigQuery) work
#   - workspace = $REC/work/cymbal-voc (starter project from production/samples/v2/build/cymbal-voc)
#   - CDP on :9334, launched in a new session so the launching shell can't kill it
# Usage: REC_ACCOUNT=<you@example.com> LAB_PROJECT_ID=<your-project-id> production/capture/agy/launch_ag_rec_voc.sh [fresh]
# Optional: AG_REC_HOME (default ~/ag-rec-voc), AG_APP (default /Applications/Antigravity.app),
#           AG_PROFILE_SRC (your app's Electron profile dir), AG_DATA_DIR (your app's ~/.gemini data dir)
set -euo pipefail
REC="${AG_REC_HOME:-$HOME/ag-rec-voc}"
SRC="${AG_PROFILE_SRC:-$HOME/Library/Application Support/Antigravity}"
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
ACCOUNT="${REC_ACCOUNT:?set REC_ACCOUNT=<the gcloud account used for MCP/ADC>}"
LAB_PROJECT_ID="${LAB_PROJECT_ID:?set LAB_PROJECT_ID=<your-project-id>}"
AG_DATA_DIR="${AG_DATA_DIR:-$HOME/.gemini/antigravity}"
AG_APP="${AG_APP:-/Applications/Antigravity.app}"
if [[ "${1:-}" == "fresh" ]]; then rm -rf "$REC"; fi
if [[ ! -d "$REC/profile" ]]; then
  mkdir -p "$REC/home/.gemini/$(basename "$AG_DATA_DIR")" "$REC/profile/User" "$REC/work"
  cp "$HOME/.gemini/google_accounts.json" "$REC/home/.gemini/" 2>/dev/null || true
  cp "$HOME/.gemini/installation_id" "$REC/home/.gemini/" 2>/dev/null || true
  for f in installation_id user_settings.pb; do cp "$AG_DATA_DIR/$f" "$REC/home/.gemini/$(basename "$AG_DATA_DIR")/" 2>/dev/null || true; done
  for d in "Local Storage" Preferences Cookies "Network Persistent State" machineid languagepacks.json; do
    [[ -e "$SRC/$d" ]] && cp -R "$SRC/$d" "$REC/profile/"
  done
  [[ -d "$SRC/User/globalStorage" ]] && rsync -a --exclude '*.backup' "$SRC/User/globalStorage" "$REC/profile/User/"
  [[ -f "$SRC/User/settings.json" ]] && cp "$SRC/User/settings.json" "$REC/profile/User/"
  [[ -f "$HOME/.gitconfig" ]] && cp "$HOME/.gitconfig" "$REC/home/.gitconfig"
fi
# the agent's sign-in token lives in the login keychain ("<App> Safe Storage"): keep it reachable from the isolated HOME
mkdir -p "$REC/home/Library"
[[ -e "$REC/home/Library/Keychains" ]] || ln -s "$HOME/Library/Keychains" "$REC/home/Library/Keychains"
# one coordinate space for DOM boxes, stills and screencast: window content exactly 1440x810 CSS px at zoom 0
python3 - "$REC/profile/User" <<'PY'
import json, os, sys
u = sys.argv[1]
sp = os.path.join(u, "settings.json")
s = json.load(open(sp)) if os.path.exists(sp) else {}
s.update({"window.zoomLevel": 0, "window.zoomPerWindow": False, "window.restoreWindows": "none",
          "window.newWindowDimensions": "default", "workbench.startupEditor": "none"})
json.dump(s, open(sp, "w"), indent=2)
gp = os.path.join(u, "globalStorage", "storage.json")
g = json.load(open(gp)) if os.path.exists(gp) else {}
ui = {"mode": 1, "x": 60, "y": 60, "width": 1440, "height": 810, "zoomLevel": 0}
g["windowsState"] = {"lastActiveWindow": {"uiState": ui}, "openedWindows": []}
os.makedirs(os.path.dirname(gp), exist_ok=True)
json.dump(g, open(gp, "w"))
print("window pinned to 1440x810 @ zoom 0")
PY
# gcloud + ADC for the isolated HOME (refreshed on every launch: reauth tokens expire)
mkdir -p "$REC/home/.config"
rsync -a --delete --exclude logs "$HOME/.config/gcloud/" "$REC/home/.config/gcloud/"
CLOUDSDK_CONFIG="$REC/home/.config/gcloud" gcloud config set account "$ACCOUNT" >/dev/null 2>&1 || true
CLOUDSDK_CONFIG="$REC/home/.config/gcloud" gcloud config set project "$LAB_PROJECT_ID" >/dev/null 2>&1 || true
python3 - "$HOME/.config/gcloud/legacy_credentials/$ACCOUNT/adc.json" "$REC/home/.config/gcloud/application_default_credentials.json" "$LAB_PROJECT_ID" <<'PY'
import json, sys
src, dst, project = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(src))
d["quota_project_id"] = project
json.dump(d, open(dst, "w"))
print("ADC ->", dst)
PY
# starter project (only if missing — recordings build on it lab by lab)
if [[ ! -d "$REC/work/cymbal-voc" ]]; then
  cp -R "$ROOT/production/samples/v2/build/cymbal-voc" "$REC/work/cymbal-voc"
  (cd "$REC/work/cymbal-voc" && git init -q && git add -A && git commit -qm "starter: Cymbal VOC (가상 데이터)" || true)
fi
if lsof -iTCP:9334 -sTCP:LISTEN >/dev/null 2>&1; then echo "already running"; exit 0; fi
# recording-machine quirk (client-certificate policy on the machine): google-auth would try mTLS endpoints and agents-cli deploy /
# eval fail on camera. Learners never see this → disable client certificates for every process the agent starts.
export GOOGLE_API_USE_CLIENT_CERTIFICATE=false
HOME="$REC/home" REC="$REC" python3 - <<'PY'
import os, subprocess
rec = os.environ["REC"]
log = open(f"{rec}/app.log", "ab")
app = os.environ.get("AG_APP", "/Applications/Antigravity.app")
exe = f"{app}/Contents/MacOS/{os.path.basename(app)[:-4]}"
if not os.path.exists(exe):
    exe = f"{app}/Contents/MacOS/Electron"
p = subprocess.Popen([exe, f"--user-data-dir={rec}/profile", "--remote-debugging-port=9334", f"{rec}/work/cymbal-voc"],
                     stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
print("started pid", p.pid)
PY
