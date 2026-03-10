import sqlite3
from http.server import BaseHTTPRequestHandler,HTTPServer

class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  conn=sqlite3.connect("disks.db")
  rows=conn.execute("select serial,reliability_score from disks").fetchall()
  metrics=""
  for r in rows:
   metrics+=f'disk_reliability_score{{serial="{r[0]}"}} {r[1]}\n'
  self.send_response(200)
  self.send_header("Content-type","text/plain")
  self.end_headers()
  self.wfile.write(metrics.encode())

HTTPServer(("",9105),Handler).serve_forever()
