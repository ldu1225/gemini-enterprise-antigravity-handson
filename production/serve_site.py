"""Local preview server for site_v2 with HTTP Range support (needed for <video> seeking).

`python3 -m http.server` ignores Range headers, so browsers cannot seek backwards/forwards in MP4s.
Usage: python3 production/serve_site.py [site_dir] [port]     (default: site_v2 8080)
"""
import os
import re
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


class RangeHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        rng = self.headers.get("Range")
        path = self.translate_path(self.path)
        if not rng or not os.path.isfile(path):
            return super().send_head()
        m = re.match(r"bytes=(\d*)-(\d*)", rng)
        size = os.path.getsize(path)
        if not m:
            return super().send_head()
        start = int(m.group(1)) if m.group(1) else max(0, size - int(m.group(2) or 0))
        end = int(m.group(2)) if m.group(1) and m.group(2) else size - 1
        end = min(end, size - 1)
        if start > end:
            self.send_error(416, "Requested Range Not Satisfiable")
            return None
        f = open(path, "rb")
        f.seek(start)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        self._remaining = end - start + 1
        return f

    def end_headers(self):
        self.send_header("Accept-Ranges", "bytes")
        # Preview must always show what is on disk: without Cache-Control the browser applied heuristic
        # caching (Last-Modified only) and kept a re-captured, same-name screenshot from an earlier visit.
        # HTML gets no-store: with no-cache, back/forward navigation and restored tabs still reuse the
        # stored page without asking the server (a morning build of ag/index.html showed up hours later).
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        is_html = path.endswith((".html", "/")) or "." not in path.rsplit("/", 1)[-1]
        self.send_header("Cache-Control", "no-store" if is_html else "no-cache")
        super().end_headers()

    def copyfile(self, source, outputfile):
        remaining = getattr(self, "_remaining", None)
        if remaining is None:
            return super().copyfile(source, outputfile)
        try:
            while remaining > 0:
                chunk = source.read(min(64 * 1024, remaining))
                if not chunk:
                    break
                outputfile.write(chunk)
                remaining -= len(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            self._remaining = None


if __name__ == "__main__":
    site = sys.argv[1] if len(sys.argv) > 1 else "site_v2"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
    host = os.environ.get("SERVE_HOST", "127.0.0.1")  # local preview only; set SERVE_HOST deliberately to expose it
    os.chdir(site)
    print(f"serving {os.getcwd()} on http://{host}:{port} (Range enabled)")
    ThreadingHTTPServer((host, port), RangeHandler).serve_forever()
