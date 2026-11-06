# deploy — static hosting on Cloud Run

The portal is plain static files (`site_v2/`), served by an unprivileged nginx container on Cloud Run.

| File | Purpose |
|---|---|
| `Dockerfile` | `nginxinc/nginx-unprivileged:1.28.0-alpine` (non-root, listens on 8080); copies the nginx config and the site |
| `nginx/default.conf` | read-only server: only `GET`/`HEAD` (others → 405), `try_files`, `text/vtt` for captions, practice files forced to download (`Content-Disposition: attachment`), dotfiles hidden, custom 404, gzip, HTTP/2 cleartext (`http2 on`), cache policy (below) |
| `nginx/security_headers.conf` | security headers included in every location (CSP and friends) |
| `deploy.sh` | stages `site_v2/` into `deploy/.build/`, refuses files > 95 MB, runs `gcloud run deploy --source` |
| `smoke_test.py` | headless Chrome against the live URL: console errors/warnings, failed requests, broken images, video readiness |

## Deploy

```bash
python3 production/site_build_v2/build.py                 # build site_v2/ first
PROJECT=your-project-id deploy/deploy.sh                    # REGION defaults to asia-northeast3, SERVICE to ge-ag-handson-lab
# optional: deploy/deploy.sh /path/to/other/site_dir
python3 deploy/smoke_test.py https://<service-url>/
```

`deploy.sh` runs `gcloud run deploy "$SERVICE" --source deploy/.build --allow-unauthenticated --port 8080
--use-http2 --cpu 1 --memory 512Mi --concurrency 250 --min-instances 0 --max-instances 4`. The content is public
training material with synthetic data; remove `--allow-unauthenticated` (and put IAP or another gate in front)
if your edition must be private. Use your own account and project — the script never changes your global
`gcloud` configuration; pass the account per command if needed (`CLOUDSDK_CORE_ACCOUNT=… deploy/deploy.sh`).

## Why HTTP/2 end to end

Cloud Run limits HTTP/1 responses to 32 MiB; several lab videos are larger. The service is deployed with
`--use-http2` and nginx speaks h2c (`http2 on`), which removes that cap. The 95 MB guard in `deploy.sh` catches
accidental raw exports.

## Caching

| Resource | `Cache-Control` | Why |
|---|---|---|
| HTML / JSON (default) | `no-cache` | HTML is the only unversioned resource; a redeploy is visible on the next page view |
| `*.css`, `*.js` | `public, max-age=3600` | URLs carry `?v=<content hash>` |
| images, fonts, `*.mp4`, `*.vtt` | `public, max-age=86400` | URLs carry `?v=<content hash>`, so re-rendered media are never served stale |

The local preview server `production/serve_site.py` (127.0.0.1 only, HTTP Range support for video seeking)
sends `no-store` for HTML and `no-cache` for everything else.

## Not rate-limited on purpose

Trainees often share one corporate NAT address, so a per-IP limit would throttle a whole classroom. Abuse and
cost are bounded by `--max-instances` and the read-only static content; add Cloud Armor if you need more.
