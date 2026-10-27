"""Job Application Tracker - local server. Python 3.8+, no dependencies.
Run:  python server.py   then open http://localhost:8000
Every change is written straight to applications.csv (next to this file)."""
import csv, io, json, os, re, threading, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "applications.csv")
FIELDS = ["id", "company", "role", "location", "date", "status", "link", "description", "notes"]
STATUSES = ["Wishlist", "Applied", "Interview", "Offer", "Rejected"]
ALIASES = {"id": "id", "company": "company", "role": "role", "title": "role", "jobtitle": "role",
           "location": "location", "date": "date", "dateapplied": "date", "status": "status",
           "link": "link", "url": "link", "description": "description",
           "jobdescription": "description", "notes": "notes"}
LOCK = threading.Lock()


def read_rows():
    if not os.path.exists(CSV_PATH):
        return []
    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
        return [{k: (r.get(k) or "") for k in FIELDS} for r in csv.DictReader(f)]


def write_rows(rows):
    tmp = CSV_PATH + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8-sig") as f:  # BOM so Excel shows accents
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, CSV_PATH)


def clean(d):
    out = {k: str(d.get(k) or "").strip()[:20000] for k in FIELDS}
    if out["status"] not in STATUSES:
        out["status"] = "Applied"
    return out


def parse_csv(text):
    reader = csv.reader(io.StringIO(text.lstrip("\ufeff")))
    header = next(reader, [])
    cols = [ALIASES.get(re.sub(r"[^a-z]", "", h.lower())) for h in header]
    rows = []
    for r in reader:
        d = {c: v for c, v in zip(cols, r) if c}
        if d.get("company") or d.get("role"):
            rows.append(clean(d))
    return rows


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body, ctype="application/json", extra=None):
        data = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n).decode("utf-8-sig")

    def guarded(self, fn):
        try:
            with LOCK:
                code, payload = fn()
            self.send(code, payload)
        except PermissionError:
            self.send(423, {"error": "applications.csv is open in another program (Excel?). Close it and try again."})
        except Exception as e:
            self.send(500, {"error": str(e)})

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            with open(os.path.join(HERE, "index.html"), "rb") as f:
                self.send(200, f.read(), "text/html")
        elif self.path == "/dashboard":
            with open(os.path.join(HERE, "dashboard.html"), "rb") as f:
                self.send(200, f.read(), "text/html")
        elif self.path == "/api/applications":
            self.guarded(lambda: (200, read_rows()))
        elif self.path == "/applications.csv":
            with LOCK:
                if not os.path.exists(CSV_PATH):
                    write_rows([])
                with open(CSV_PATH, "rb") as f:
                    data = f.read()
            self.send(200, data, "text/csv", {"Content-Disposition": 'attachment; filename="applications.csv"'})
        else:
            self.send(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/api/applications":
            def add():
                d = clean(json.loads(self.body()))
                if not (d["company"] and d["role"]):
                    return 400, {"error": "company and role are required"}
                d["id"] = uuid.uuid4().hex[:8]
                rows = read_rows()
                rows.append(d)
                write_rows(rows)
                return 201, d
            self.guarded(add)
        elif self.path == "/api/import":
            def imp():
                rows = read_rows()
                seen = {(r["company"].lower(), r["role"].lower(), r["date"]) for r in rows}
                ids = {r["id"] for r in rows}
                added = skipped = 0
                for r in parse_csv(self.body()):
                    key = (r["company"].lower(), r["role"].lower(), r["date"])
                    if key in seen:
                        skipped += 1
                        continue
                    if not r["id"] or r["id"] in ids:
                        r["id"] = uuid.uuid4().hex[:8]
                    seen.add(key); ids.add(r["id"]); rows.append(r); added += 1
                if added:
                    write_rows(rows)
                return 200, {"added": added, "skipped": skipped}
            self.guarded(imp)
        else:
            self.send(404, {"error": "not found"})

    def do_PUT(self):
        m = re.fullmatch(r"/api/applications/(\w+)", self.path)
        if not m:
            return self.send(404, {"error": "not found"})

        def upd():
            changes = json.loads(self.body())
            rows = read_rows()
            for r in rows:
                if r["id"] == m.group(1):
                    r.update(clean({**r, **changes}))
                    write_rows(rows)
                    return 200, r
            return 404, {"error": "not found"}
        self.guarded(upd)

    def do_DELETE(self):
        m = re.fullmatch(r"/api/applications/(\w+)", self.path)
        if not m:
            return self.send(404, {"error": "not found"})

        def rem():
            rows = [r for r in read_rows() if r["id"] != m.group(1)]
            write_rows(rows)
            return 200, {"ok": True}
        self.guarded(rem)


if __name__ == "__main__":
    if not os.path.exists(CSV_PATH):
        write_rows([])
    print("Job tracker running at http://localhost:8000  (Ctrl+C to stop)")
    print("Data file:", CSV_PATH)
    ThreadingHTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
