"""
    Program to obtain latest Inverter data using Givenergy Cloud API

"""
import configparser as c
import requests

ofName = "inverterSettingsValidation.csv"

config = c.ConfigParser()
config.read('GivEnergyConfig.ini')

API_token = config['DEFAULT']['api_token']
inverterID = config['DEFAULT']['inverterid']

url = 'https://api.givenergy.cloud/v1/inverter/'+inverterID+'/system-data/latest'
headers = {
    "Authorization": "Bearer " + API_token,
    "Content-Type": "application/json",
    "Accept": "application/json",
}

print("Getting Latest data...")
r = requests.get(url, headers=headers)
systemData = r.json()
print (systemData)

print('Battery SOC:', systemData["data"]["battery"]["percent"])
