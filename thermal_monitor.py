import subprocess,time,sqlite3

DB="disks.db"

def read_temp(device):
 try:
  out=subprocess.check_output(["smartctl","-A",device]).decode()
  for line in out.splitlines():
   if "Temperature" in line:
    return int(line.split()[-1])
 except:
  return None

def monitor(device,serial):
 conn=sqlite3.connect(DB)
 while True:
  t=read_temp(device)
  if t:
   conn.execute("insert into temperature_history(serial,temperature,timestamp) values(?,?,datetime('now'))",(serial,t))
   conn.commit()
  time.sleep(60)
