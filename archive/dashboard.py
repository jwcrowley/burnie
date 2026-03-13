import sqlite3
from http.server import BaseHTTPRequestHandler,HTTPServer

DB="disks.db"

class Handler(BaseHTTPRequestHandler):

 def do_GET(self):
  conn=sqlite3.connect(DB)
  rows=conn.execute("select serial,model,reliability_score,last_test from disks").fetchall()

  html="<h1>Disk Reliability Lab v6</h1>"
  html+="<table border=1>"
  html+="<tr><th>Serial</th><th>Model</th><th>Score</th><th>Last Test</th></tr>"

  for r in rows:
   html+=f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td></tr>"

  html+="</table>"

  self.send_response(200)
  self.send_header("Content-type","text/html")
  self.end_headers()
  self.wfile.write(html.encode())

HTTPServer(("",8080),Handler).serve_forever()
