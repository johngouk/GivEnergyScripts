"""
    Program to modify current Eco Inverter setting using Givenergy Cloud API
    Modified for Python 3.4.2 isoformat() sig
    Usage:
        python GivEnergyEcoModeSet.py [-v] [ON|OFF]
"""
import requests
import datetime
import argparse
    
API_token = "<put API token here>"

ID_Eco = "24"
action_write = "write"
action_read = "read"


parser = argparse.ArgumentParser(prog='setEcoState')
parser.add_argument("newState", help="New Inverter Eco State - ON/OFF")
parser.add_argument("-v", "--verbosity", help="increase output verbosity",
    action = "store_true")
args = parser.parse_args()
verbose = False
if args.verbosity:
    verbose = True
newStateArg = args.newState
newStateArg = newStateArg.upper()
newStateVal = True
if (newStateArg=='ON'):
    newStateVal = True
elif (newStateArg=='OFF'):
    newStateVal = False
else:
    print('newState must be "ON" or "OFF"!')
    exit(1)

url = "https://api.givenergy.cloud/v1/inverter/<your Inverter ID>/settings"
headers = {
    "Authorization": "Bearer " + API_token,
    "Content-Type": "application/json",
    "Accept": "application/json",
}

if verbose:
    timeStamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    print(timeStamp + " - " + "Getting Inverter Eco Status... ", end="")

r = requests.post(url + "/" + ID_Eco + "/" + action_read, headers=headers)
settings = r.json()
if verbose:
    print(str(settings["data"]["value"]))

currentSetting = settings["data"]["value"]

newSetting = newStateVal
if newSetting != currentSetting:
    if verbose:
        timeStamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        print(timeStamp + " - " + "Setting Inverter Eco Status...", str(newSetting))
        newSettingJSON = {"value": str(newSetting).lower()}

        r = requests.post(
        url + "/" + ID_Eco + "/" + action_write, headers=headers, json=newSettingJSON
        )
        result = r.json()
        # print(str(result))

        timeStamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if result["data"]["success"] == True and result["data"]["value"] == newSetting:
            if verbose:
                print(timeStamp + " - " + "Inverter Eco Status Change Successful")
            else:
                print(
                timeStamp
                + " - "
                + "Inverter Eco Status Change Failed:"
                + result["data"]["message"]
                )
