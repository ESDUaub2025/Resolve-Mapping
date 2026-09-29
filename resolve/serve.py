"""Local web server for the map.

public    serves public/ exactly as GitHub Pages does.
research  serves the same app, but /data/ comes from the private research release
          (<private store>/build/research/data): identifiable respondent records.
Always bound to 127.0.0.1 so the research view is never exposed on the network.
"""
import functools
import http.server
from pathlib import Path

from .paths import PUBLIC, private_root


class _Handler(http.server.SimpleHTTPRequestHandler):
    data_dir: Path = None

    def translate_path(self, path):
        clean = path.split("?", 1)[0].split("#", 1)[0]
        if self.data_dir is not None and clean.startswith("/data/"):
            target = (self.data_dir / clean[len("/data/"):]).resolve()
            if self.data_dir.resolve() not in target.parents:
                return str(self.data_dir / "__forbidden__")
            return str(target)
        return super().translate_path(path)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def serve(tier="research", port=8000):
    data_dir = None
    if tier == "research":
        data_dir = private_root() / "build" / "research" / "data"
        if not (data_dir / "catalog.json").exists():
            raise SystemExit("Research release not built yet: run  python -m resolve build --tier research")
    handler = functools.partial(type("Handler", (_Handler,), {"data_dir": data_dir}), directory=str(PUBLIC))
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as httpd:
        print(f"RESOLVE {tier} map on http://127.0.0.1:{port}/  (Ctrl+C to stop)")
        if tier == "research":
            print("This view shows personal data. Keep it on this machine.")
        httpd.serve_forever()
