"""
    Program to collect Inverter settings using Givenergy Cloud API

"""
import configparser as c
import requests
import csv
from datetime import datetime, time, date, timedelta
import urllib.parse

today = datetime.now()
timeStr = str(today.time()).replace(':','.')
ofName = "inverterSettings_"+str(today.date())+"_"+timeStr+".csv"

config = c.ConfigParser()
config.read('GivEnergyConfig.ini')

API_token = config['DEFAULT']['api_token']
inverterID = config['DEFAULT']['inverterid']

url = 'https://api.givenergy.cloud/v1/inverter/'+inverterID+'/settings'
headers = {
    "Authorization": "Bearer " + API_token,
    "Content-Type": "application/json",
    "Accept": "application/json",
}

action_write = "write"
action_read = "read"

print("Getting Settings list...")
r = requests.get(url, headers=headers)
settings = r.json()
fieldNames = ["id","name","validation_rules","validation"]
print("ID,Name,Value")
with open(ofName, "w", encoding="utf-8", newline='') as csvfile:
    #csvOut = csv.DictWriter(csvfile, dialect='excel', fieldnames=fieldNames)
    #csvOut.writeheader()
    csvfile.write("ID,Name,Value\n")
    for setting in settings["data"]:
        # Get the setting...
        r = requests.post(
            url + "/" + str(setting["id"]) + "/" + action_read, headers=headers
        )
        settingData = r.json()
        print(str(setting["id"]), str(setting["name"]), str(settingData["data"]["value"]), sep=',')
#        csvOut.writerow(setting["id"], setting["name"], setting["validation_rules"][0], setting["validation"])
#        csvOut.writerow({setting["id"], setting["name"], setting["validation_rules"][0], setting["validation"]})
#        csvOut.writerow(settin
        csvfile.write(str(setting["id"])+','+str(setting["name"])+','+str(settingData["data"]["value"])+'\n')
csvfile.close()
