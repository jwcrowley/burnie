import glob,statistics,sqlite3,os

DB="disks.db"

def analyze(serial):

 files=glob.glob(f"artifacts/{serial}/latency*")
 values=[]

 for f in files:
  with open(f) as fh:
   for line in fh:
    parts=line.split()
    if len(parts)>1:
     values.append(float(parts[-1]))

 if not values:
  return

 p99=statistics.quantiles(values,n=100)[98]

 if p99>50:
  conn=sqlite3.connect(DB)
  conn.execute("insert into latency_anomalies(serial,latency_ms,timestamp) values(?,?,datetime('now'))",(serial,p99))
  conn.commit()
