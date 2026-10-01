#!/usr/bin/env python3
"""Serve only the reviewed bundle on loopback, to the target Wikibase origin."""
from http.server import BaseHTTPRequestHandler,HTTPServer
from pathlib import Path
ROOT=Path(__file__).resolve().parent
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  if self.path not in ('/execute.js','/finish.js','/catalogue.js'):self.send_error(404);return
  data=(ROOT/self.path[1:]).read_bytes()
  self.send_response(200);self.send_header('Content-Type','application/javascript; charset=utf-8');self.send_header('Access-Control-Allow-Origin','https://ephemera-poc.wikibase.cloud');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
 def log_message(self,*args):pass
print('Serving reviewed code on http://127.0.0.1:8765/execute.js',flush=True)
HTTPServer(('127.0.0.1',8765),Handler).serve_forever()
