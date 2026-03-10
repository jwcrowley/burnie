from fastapi import FastAPI
import sqlite3

app=FastAPI()

@app.get("/disks")
def disks():
 conn=sqlite3.connect("disks.db")
 rows=conn.execute("select serial,model,reliability_score from disks").fetchall()
 return [{"serial":r[0],"model":r[1],"score":r[2]} for r in rows]

@app.get("/stats/models")
def model_stats():
 conn=sqlite3.connect("disks.db")
 rows=conn.execute("select model,avg(reliability_score) from disks group by model").fetchall()
 return [{"model":r[0],"avg_score":r[1]} for r in rows]
