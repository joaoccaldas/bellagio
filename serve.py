"""Static server for web/dist + POST /snap (dataURL JPEG) -> renders/web/<name>.jpg for screenshot review."""
import http.server, base64, os, json, sys
ROOT = os.path.dirname(os.path.abspath(__file__))
DIST, SNAP = os.path.join(ROOT, 'web', 'dist'), os.path.join(ROOT, 'renders', 'web')
os.makedirs(SNAP, exist_ok=True)
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=DIST, **k)
    def do_POST(self):
        if self.path.startswith('/snap'):
            d = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            name = ''.join(c for c in d.get('name', 'snap') if c.isalnum() or c in '-_')[:60]
            open(os.path.join(SNAP, name + '.jpg'), 'wb').write(base64.b64decode(d['data'].split(',', 1)[1]))
            self.send_response(200); self.end_headers(); self.wfile.write(b'ok')
        else:
            self.send_response(404); self.end_headers()
    def log_message(self, *a): pass
http.server.ThreadingHTTPServer(('127.0.0.1', int(sys.argv[1]) if len(sys.argv) > 1 else 8793), H).serve_forever()
