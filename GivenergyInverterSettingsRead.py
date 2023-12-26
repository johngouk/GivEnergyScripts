"""

    Program to get/set a specific ID setting in the Givenergy Portal

    Uses a CSV config file that holds the valid (as recently acquired!) settings, validation rules and notes

"""
import configparser as c
import csv
import requests
from datetime import datetime, time, date, timedelta

verbosity = 1


action_write = "write"
action_read = "read"

def printVerbose(thing):
    if verbosity > 0:
        print(thing)


def getAvailableSettings():
    # Load the setting list
    settingList = {}
    ofName = "/Users/john/Downloads/inverterSettings.csv"
    with open(ofName, "r", encoding="utf-8", newline="") as csvfile:
        csvIn = csv.DictReader(csvfile, dialect="excel")
        for row in csvIn:
            settingList[row["id"]] = {
                "name": row["name"],
                "rules": row["validation_rules"],
                "val": row["validation"],
            }
            printVerbose(
                row["id"]
                + " "
                + row["name"]
                + " "
                + row["validation_rules"]
                + " "
                + row["validation"]
            )
        printVerbose("Loaded " + str(len(settingList)) + " items")
    csvfile.close()
    return settingList


def printIDList(settingList):
    for s in settingList.items():
        print(s[0], s[1]["name"], sep=":")


def getSettingID(availableSettings):
    reqID = 0
    IDprovided = False
    while not IDprovided:
        reqIDin = input("Enter ID to get/set (Enter for list) -> ")
        if reqIDin == "":
            printIDList(availableSettings)
        elif reqIDin.isdecimal():
            reqID = int(reqIDin)
            if str(reqID) in availableSettings:
                IDprovided = True
                # print(settingList[reqIDin])
                s = availableSettings[reqIDin]
                print(
                    'Setting Info: Name:"', s["name"],
                    '" ID:', reqIDin,
                    " Format:", s["rules"],
                    ' Notes:"', s["val"], '"',
                    sep="",
                )
            else:
                print("Valid ID please!")
        else:
            print("Numeric ID please!!")
    return reqID


def getCurrentValue(id):
    print("Getting Inverter Setting ID:", str(id), "...", end="")
    getUrl = url + "/" + str(id) + "/" + action_read
    printVerbose("GET URL: " + getUrl)

    r = requests.post(getUrl, headers=headers)
    settings = r.json()
    printVerbose("Raw setting data: " + str(settings))
    value = str(settings["data"]["value"])
    print("currently", value)
    return value


def getNewValue(reqID, validationRule):
    newValue = ""
    while newValue == "":
        newValueIn = input(
            "Enter new value for ID " + str(reqID) + ": (" + validationRule + ") -> "
        )
        printVerbose("You entered: " + newValueIn)

        newValue = validateNewValue(newValueIn, validationRule)
        printVerbose("Validated Value: " + newValue)
    return newValue


#   Returns a string of properly formatted valid text to use in the command
def validateNewValue(value, rule):

    # rule ::= "[" [ mode "," ] "'" type "']"
    # mode ::= "'writeonly'"
    # type ::= "boolean" | "in" ":" enumeration | "between" ":" range_limits | "date_format" ":" date_format | "exact" ":" integer
    # enumeration ::= integer [ "," integer ]*
    # range_limits ::= start "," end
    # start, end, exact_value ::= integer
    # date_format ::= "H:i"
    # integer ::= 0-100
    # Examples:
    #   date: "['date_format:H:i']"
    #   range: "['between:0,100']"
    #   enumeration: "['in:0,1,2']"
    #   boolean: "['boolean']"
    #   mode + type: "['writeonly', 'exact:100']"

    returnValue = ""
    # Extract rule components
    # Is it [mode][type]?
    # Remove whitespace as well as crappy "'" - you never know!
    step = 0
    rule = rule.strip().replace("'", "")
    # printVerbose(str(step) + ":" + rule)

    # step = step + 1
    rule = rule.lstrip("[").rstrip("]")
    # printVerbose(str(step) + ":" + rule)
    # Check for mode, currently only "writeonly"
    mode = ""
    writeOnly = False
    if rule.startswith("writeonly"):  # yuk
        writeOnly = True
        # "writeonly', 'exact:100"
        # Split into mode + type
        # type[0] = mode, type[1] = ",", type[2] = type
        step = step + 1
        parts = rule.partition(",")
        mode = parts[0]
        formatdef = parts[2].strip()  #  Format def has some spaces in it!
    else:
        formatdef = rule
    printVerbose(str(step) + ": Mode: '" + mode + "' Format: '" + formatdef + "'")
    # Just a type get the parts
    step = step + 1
    chunks = formatdef.partition(":")
    # chunks[0] = thing, chunks[1] = ":", chunks[2] = validation
    type = chunks[0]
    validation = chunks[2]
    printVerbose(str(step) + ": '" + type + "': " + validation)
    if type == "boolean":
        printVerbose("handling boolean")
        # Must be "true" or "false"
        value = value.lower()
        if value == "true" or value == "false":
            returnValue = value
        else:
            # oops
            print("Expecting boolean:", value)

    elif type == "date_format":
        printVerbose("handling date_format")
        # "H:i" => "HH:MM"
        H_M = value.partition(":")
        hours = H_M[0]
        mins = H_M[2]
        if not hours.isdecimal() or not mins.isdecimal():
            print("Time must be 'HH:MM'")
        elif int(hours) < 0 or int(hours) > 23:
            print("00 < HH < 23 please!")
        elif int(mins) < 0 or int(mins) > 59:
            print("00 < MM < 59 please!")
        # Reformat to exactly "HH:MM"
        else:
            returnValue = "%(h)02d:%(m)02d" % {"h": int(hours), "m": int(mins)}

    elif type == "between":
        printVerbose("handling between")
        # Value has to be numeric, decimal
        if not value.isdecimal():
            print("Value has to be a decimal integer")
        else:
            valueInt = int(value)
            # What are the limits??
            range_limits = validation.partition(",")
            if not range_limits[0].isdecimal() or not range_limits[2].isdecimal():
                print(
                    "Config error: Validation specifier for range limits must be nn,mm!!"
                )
            else:  # Set up the limits
                start = int(range_limits[0])
                end = int(range_limits[2])
                if valueInt < start or valueInt > end:
                    print(
                        "Value must be in range", range_limits[0], "-", range_limits[2]
                    )
                else:
                    returnValue = value

    elif type == "exact":
        # validation should be the permitted integer
        printVerbose("handling exact")
        if not validation.isdecimal():
            print("Config error: 'exact' value not an integer -", validation)
        elif not value.isdecimal():
            print("Value has to be a decimal integer")
        elif int(value) != int(validation):
            print("Value not= to 'exact' value -", value, " vs.", validation)
        else:
            returnValue = value

    elif type == "in":
        printVerbose("handling in")
        # Value is an integer, in the enumeration "x,y,z"
        # Analyse enumeration
        theList = validation.split(",")
        enum = []
        if len(theList) < 1:
            print("Config error: enum list no entries!" + validation)
        else:
            for x in theList:
                if not x.isdecimal():
                    print("Config error: enum list has non-decimal entry!" + validation)
                else:
                    enum.append(int(x))
            if not value.isdecimal():
                print("Value must be an integer!")
            elif int(value) not in enum:
                print("Value", value, " must be in", validation)
            else:
                returnValue = value

    else:  # WTAF? They cheated
        print("Unknown format code:", type)
        returnValue = "you're having a laugh"

    return returnValue


# ******************************* Main ************************* #

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

availableSettings = getAvailableSettings()

reqID = getSettingID(availableSettings)

currentValue = getCurrentValue(reqID)

rule = availableSettings[str(reqID)]["rules"]
name = availableSettings[str(reqID)]["name"]
printVerbose("Validation rule: " + rule)

# Now the really tricky bit - get the new value, and validate using the stuff in the list...
newValue = getNewValue(reqID, rule)

print("Setting ID", str(reqID), name, "to", newValue)
# Now need to construct and submit the setting change request
