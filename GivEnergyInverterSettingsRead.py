"""
    Program to list Inverter settings using Givenergy Cloud API

    The output file from this is used by other scripts to control
    the validation of requested changes to settings

"""
import configparser as c
import requests
import csv
from datetime import datetime, time, date, timedelta
import urllib.parse

ofName = "inverterSettingsValidation.csv"

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
        csvOut.writerow(setting)
csvfile.close()
