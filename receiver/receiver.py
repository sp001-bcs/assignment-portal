import json, os
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.getenv("RECEIVER_PORT", "5001"))
TOKEN = os.getenv("RECEIVER_TOKEN", "")
OUT_FILE = os.getenv("REPORT_PATH", "testreport.json")


class Handler(BaseHTTPRequestHandler):
    def _reply(self, code, text):
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(text.encode())

    def do_GET(self):
        self._reply(200, "Receiver is running")

    def do_POST(self):
        if self.path != "/report":
            return self._reply(404, "Not found")
        if TOKEN and self.headers.get("X-Token") != TOKEN:
            return self._reply(401, "Invalid token")
        length = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(length))
        except json.JSONDecodeError:
            return self._reply(400, "Body is not valid JSON")

        with open(OUT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.makedirs("reports", exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        with open(f"reports/{stamp}-run{data.get('pipeline_run_id', 'x')}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        s = data.get("summary", {})
        print(f"[{datetime.now():%H:%M:%S}] Report received | commit {str(data.get('commit_sha'))[:7]} | "
              f"{s.get('overall_status')} | {s.get('passed')}/{s.get('total')} passed")
        self._reply(200, "Saved")


if __name__ == "__main__":
    print(f"Receiver listening on port {PORT}")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
