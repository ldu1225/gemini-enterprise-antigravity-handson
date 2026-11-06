#!/usr/bin/env bash
# Deploy the static lab portal to Cloud Run (nginx container, strict CSP).
# Usage: PROJECT=<your-project-id> [REGION=asia-northeast3] [SERVICE=ge-ag-handson-lab] deploy/deploy.sh
set -euo pipefail

PROJECT="${PROJECT:?set PROJECT=<your-project-id>}"
REGION="${REGION:-asia-northeast3}"
SERVICE="${SERVICE:-ge-ag-handson-lab}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SITE_DIR="${1:-$ROOT/site_v2}"
BUILD="$ROOT/deploy/.build"

test -f "$SITE_DIR/index.html" || { echo "$SITE_DIR/index.html missing — run the site build first" >&2; exit 1; }

rm -rf "$BUILD"
mkdir -p "$BUILD"
cp "$ROOT/deploy/Dockerfile" "$BUILD/"
cp -R "$ROOT/deploy/nginx" "$BUILD/nginx"
rsync -a --delete --exclude '.DS_Store' --exclude '*.map' --exclude '*.part.mp4' --exclude 'sample_*' "$SITE_DIR/" "$BUILD/site/"
du -sh "$BUILD/site"

# Cloud Run caps HTTP/1 responses at 32 MiB; the service therefore runs end-to-end HTTP/2 (--use-http2,
# nginx "http2 on" = h2c), which has no such cap — verified with a 40 MiB file on a tagged revision.
# Keep a sanity cap so an accidental master/raw export never ships.
TOO_BIG="$(find "$BUILD/site" -type f -size +95000k)"
if [[ -n "$TOO_BIG" ]]; then
  echo "assets over 95 MB — re-encode them first:" >&2
  echo "$TOO_BIG" >&2
  exit 1
fi

gcloud run deploy "$SERVICE" \
  --project "$PROJECT" --region "$REGION" \
  --source "$BUILD" \
  --allow-unauthenticated \
  --port 8080 --use-http2 --cpu 1 --memory 512Mi \
  --concurrency 250 --min-instances 0 --max-instances 4 \
  --quiet

gcloud run services describe "$SERVICE" --project "$PROJECT" --region "$REGION" --format 'value(status.url)'
