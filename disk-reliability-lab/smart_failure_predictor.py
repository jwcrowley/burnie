import json

def score(smart):
 score=100
 for attr in smart.get("ata_smart_attributes",{}).get("table",[]):
  name=attr["name"]
  val=attr["raw"]["value"]
  if name=="Reallocated_Sector_Ct" and val>0:
   score-=40
  if name=="Current_Pending_Sector" and val>0:
   score-=40
  if name=="Offline_Uncorrectable" and val>0:
   score-=40
 return max(score,0)
