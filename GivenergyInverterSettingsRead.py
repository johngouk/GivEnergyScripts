"""
    Program to list Inverter settings using Givenergy Cloud API

"""
import requests
import csv
from datetime import datetime, time, date, timedelta
import urllib.parse

ofName = "inverterSettings.csv"

API_token = "<your API token>"

url = "https://api.givenergy.cloud/v1/inverter/<your Inverter ID>/settings"
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
