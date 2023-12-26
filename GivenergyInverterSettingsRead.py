"""
    Program to list Inverter settings using Givenergy Cloud API

"""
import requests
import csv
from datetime import datetime, time, date, timedelta
import urllib.parse

ofName = "/Users/john/Downloads/inverterSettings.csv"

API_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI5NTc3MDIxOS1jYWE2LTRmOTctOTE3Ni0zNDBlZGMzZDQxNTgiLCJqdGkiOiJhNDY3MWNjZTlmN2FkNzhjNTcxMTAwMThhMDU1OGZmZDJkYjI0YjIwZmFkZmE2ZGY1YTQ0NmZmMDg5YzE5NmYzNWJmODVmYzZiMTcwNTgxNSIsImlhdCI6MTY5OTAxODA0MS42NTk1MjYsIm5iZiI6MTY5OTAxODA0MS42NTk1MywiZXhwIjozMjUwMzY4MDAwMC4wMDkwNiwic3ViIjoiNTQ1ODEiLCJzY29wZXMiOlsiYXBpIl19.pGWrdb-QuRDlDuLo08LXgcKs8p2Ak54vu9AiNDsctldc144ZCXOZNClkoygazlhRcJJab4c3qWbre6H_bbpq-g"

url = "https://api.givenergy.cloud/v1/inverter/FD2327G421/settings"
headers = {
    "Authorization": "Bearer "+API_token,
    "Content-Type": "application/json",
    "Accept": "application/json"
}

print("Getting Settings list...")
r = requests.get(url, headers=headers)
settings = r.json()
fieldNames = ["id","name","validation_rules","validation"]
print("ID,Name,Validation Rules,Validation")
with open(ofName, "w", encoding="utf-8", newline='') as csvfile:
    csvOut = csv.DictWriter(csvfile, dialect='excel', fieldnames=fieldNames)
    csvOut.writeheader()
    for setting in settings["data"]:
        print(setting["id"], setting["name"], setting["validation_rules"][0], setting["validation"], sep=',')
#        csvOut.writerow(setting["id"], setting["name"], setting["validation_rules"][0], setting["validation"])
#        csvOut.writerow({setting["id"], setting["name"], setting["validation_rules"][0], setting["validation"]})
        csvOut.writerow(setting)
csvfile.close()
