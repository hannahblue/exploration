#!/usr/bin/env python3
"""
serve.py — local dev server for wander

Serves the frontend and proxies elaboration requests to Claude API.
Requires: pip install anthropic
Usage:    ANTHROPIC_API_KEY=sk-... python serve.py
          then open http://localhost:8000
"""

import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler

import anthropic

SYSTEM = """\
You are a voice in a collaborative poem. You receive fragments from a word-wanderer \
— associative, drifting language — and a line added by a human reader. \
Write 2–4 lines that elaborate on the human's addition, drawing on the wanderer's \
imagery where it feels true. Be spare. Short lines. No explanation, no summary, \
no commentary. Output only the poem lines, nothing else."""


class Handler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/api/elaborate":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length))
                stanza = body.get("stanza", "").strip()
                user_line = body.get("userLine", "").strip()

                print(f"[elaborate] {len(stanza.splitlines())} wanderer lines · user: "{user_line[:60]}"")

                client = anthropic.Anthropic()
                msg = client.messages.create(
                    model="claude-opus-4-6",
                    max_tokens=200,
                    system=SYSTEM,
                    messages=[{
                        "role": "user",
                        "content": f"Wanderer's fragments:\n{stanza}\n\nHuman adds:\n{user_line}"
                    }],
                )
                elaboration = msg.content[0].text.strip()
                self._json(200, {"elaboration": elaboration})

            except Exception as e:
                print(f"[error] {e}")
                self._json(500, {"error": str(e)})
        else:
            self.send_response(404)
            self.end_headers()

    def _json(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        # suppress 200/304 noise, show everything else
        if str(args[1]) not in ("200", "304"):
            super().log_message(fmt, *args)


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("warning: ANTHROPIC_API_KEY not set — elaboration will fail")
    port = int(os.environ.get("PORT", 8000))
    print(f"wander → http://localhost:{port}")
    HTTPServer(("", port), Handler).serve_forever()
