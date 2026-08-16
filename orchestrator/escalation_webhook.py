"""Escalation voice webhook (stdlib, zero deps). Twilio <Gather> POSTs the caller's
DTMF/speech here; we write the answer back, LOG THE TRANSCRIPT, speak a confirmation.
Cloudflare-robust: HTTP/1.1 + explicit Content-Length. GET / is a health check.
"""
import os, json, urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timezone
import escalation

HERE = os.path.dirname(os.path.abspath(__file__))
TRANSCRIPTS = os.path.join(HERE, "state", "call_transcripts.jsonl")
VOICE = os.environ.get("WITCH_VOICE", "Polly.Amy-Neural")

def _log(entry):
    entry["utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with open(TRANSCRIPTS, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def process_gather(esc, digits, speech, frm="", callsid=""):
    answer_val = (digits or speech or "").strip()
    if esc and answer_val:
        result = escalation.answer(esc, answer_val)
        _log({"esc": esc, "digits": digits, "speech": speech, "from": frm, "callsid": callsid, "result": result})
        spoken = " ".join(answer_val) if answer_val.isdigit() else answer_val
        return f"Got it. {spoken}. Recorded and blessed. Goodbye."
    _log({"esc": esc, "digits": digits, "speech": speech, "from": frm, "callsid": callsid, "result": "no answer captured"})
    return "I did not catch that. Please text the number instead. Goodbye."

class _H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def _send(self, payload, ctype="text/xml"):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(payload)
    def do_GET(self):
        self._send(b"eos escalation webhook: OK", "text/plain")
    def do_POST(self):
        q = urllib.parse.urlparse(self.path)
        esc = (urllib.parse.parse_qs(q.query).get("esc") or [""])[0]
        n = int(self.headers.get("Content-Length", 0) or 0)
        form = urllib.parse.parse_qs(self.rfile.read(n).decode()) if n else {}
        spoken = process_gather(esc,
                                (form.get("Digits") or [""])[0],
                                (form.get("SpeechResult") or [""])[0],
                                (form.get("From") or [""])[0],
                                (form.get("CallSid") or [""])[0])
        body = f'<?xml version="1.0" encoding="UTF-8"?><Response><Say voice="{VOICE}">{spoken}</Say></Response>'
        self._send(body.encode())
    def log_message(self, fmt, *a):
        print("[webhook]", fmt % a)   # show hits so we can SEE Twilio reach us

def serve():
    port = int(os.environ.get("EOS_WEBHOOK_PORT", "8091"))
    print(f"escalation webhook listening on :{port}")
    HTTPServer(("0.0.0.0", port), _H).serve_forever()

if __name__ == "__main__":
    serve()
