'''
    Solcast Solar forecast and actuals data collection programme

    Two arrays, Eastside and Westside
    Forecast is a JSON structure:
    {"forecasts":[
        {
			"pv_estimate": 0.7899,
			"pv_estimate10": 0.6236,
			"pv_estimate90": 0.9684,
			"period_end": "2024-06-01T13:00:00.0000000Z",
			"period": "PT30M"
		},... ]
    }
    containing 30m Power numbers: estimate, 10% and 90% confidence
    I want to build a day (00:00-23:59) picture of the Power likely to arrive
    Programme runs the day before (before midnight), so gets data for Today + 1
    It also collects the GivEnergy Inverter data for the current day, using the GivEnergy Cloud API.
    Although this is not as accurate as collecting data from the inverter at 10 sec intervals,
    it does provide a consistent basis for comparing forecasts and actuals.

    Data is saved in a siple SQLite3 database table:
    Date    PVForecast PVActual Ratio
    d-1     n(d-1)      m(d-1)  n/m     Initial entry on d-2, completed on d-1
    d       n(d)        m(d)    n/m     Initial entry on d-1, completed on d
    d+1     n(d+1)      --      --      Initial entry on d+1, will be completed on d+1

'''

import json
import os
import datetime
import time
import requests
import logging
import sys
import configparser as c
import argparse

#import plotly.express as px
#import pandas as pd

import sqlite3
from urllib.request import pathname2url

'''

sqlite> select sql from sqlite_schema where name = 'dataseries';
>>> CREATE TABLE dataseries (date STRING, PVForecast REAL, PVActual REAL, Ratio REAL)

'''

def sumPower (data, day):
    # 'data' is a list of forecast data lists from Solcast, as described e.g. [fcast1, fcast2,...]
    # day is the ordinal number of the day we want a forecast for, to eliminate boundary entries,
    #   although that probably woudln't matter as at night they are 0.0 anyway!
    # totalPower is the sum of all non-zero entries for all provided forecasts
    totalPower = 0.0
    fcastCount = 0
    datumCount = 0
    for d in data:
        fcastCount = fcastCount + 1
        for x in d["forecasts"]:
            ts = x["period_end"][0:26] # "2024-06-01T13:00:00.0000000Z"
            dayNum = datetime.date.fromisoformat(ts[0:10]).toordinal()
            if dayNum == day: # Add it up
                datumCount = datumCount + 1
                totalPower = totalPower + float(x["pv_estimate"])
                # print (fcastCount, datumCount, ts, dayNum, totalPower)
    return totalPower

def getForecast(urls):
    # 'urls' is a list of URLs
    # 'data' is a list of arrays of forecast data structures
    headers = {
        "Authorization": "Bearer " + SC_API_token,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    data = []
    # print("Getting Latest data...")
    for u in urls:                              # For each URL...
        r = requests.get(u, headers=headers)    # get the forecast
        print(str(r))
        if (r.ok) and (len(r.content) != 0):    # If forecast returned...
            data.append(r.json())               # Append it to the returned list
        else:
            print("SolCast req error", str(r.status_code), r.reason)
            logger.error("SolCast req error " + str(r.status_code) + " " + r.reason)
            data.append({})                     # If none, return enpty structure
    return data

def getFilecast(fileNames):
    # 'fileNames' is a list of filenames
    # 'data' is a list of arrays of forecast data structures
    data = []
    for fn in fileNames:            # For each file...
        fd = open(fn, mode='rt')
        data.append(json.load(fd))  # decode and append the data
        fd.close()
    return data

def getPVActuals(dateRequired):
    url = 'https://api.givenergy.cloud/v1/inverter/' + inverterID + '/energy-flows'
    start_date = dateRequired.isoformat()
    end_date = datetime.date.fromordinal(dateRequired.toordinal()+1).isoformat() # Probably an easier way to get this!
    payload = {
        "start_time": start_date,
        "end_time": end_date,
        "grouping": 1,
        "types": [
            0,
            1,
            2,
            3,
            4,
            5,
            6
        ]
    }
    headers = {
      'Authorization': 'Bearer ' + GE_API_token,
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    }

    response = requests.request('POST', url, headers=headers, json=payload)
    info = response.json()
    '''
        info is of form
        {'data':
            {'0': {'start_time': '2023-10-18 00:00', 'end_time': '2023-10-19 00:00',
                'data': {'0': 1.5900000000000003, '1': 0, '2': 0, '3': 2.549999999999999, '4': 10.459999999999999, '5': 8.309999999999999, '6': 0.7900000000000003}
                },
             '1': {'start_time': '2023-10-19 00:00', 'end_time': '2023-10-20 00:00',
                'data': {'0': 4.369999999999999, '1': 1.0900000000000003, '2': 0, '3': 14.3, '4': 0.09, '5': 1.4900000000000004, '6': 0},
            }
                    }
        }
    '''
    x = info['data']['0']['data']
    # X = {'0': 1.593, '1': 0, '2': 0, '3': 2.549, '4': 10.459, '5': 8.309, '6': 0.793}
    data = {}
    data["PV_Home"] = x["0"]
    data["PV_Batt"] = x["1"]
    data["PV_Grid"] = x["2"]
    data["Grid_Home"] = x["3"]
    data["Grid_Batt"] = x["4"]
    data["Batt_Home"] = x["5"]
    data["Batt_Grid"] = x["6"]
    data["PV_Total"] = x["0"] + x["1"] + x["2"]
    data["Home_Total"] = x["0"] + x["3"] + x["5"]
    data["Import_Total"] = x["3"] + x["4"]
    data["Export_Total"] = x["2"] + x["6"]
    return data

def openDatabase(filename):
    try:
        # connect to the database in rw mode so we can catch the error if it doesn't exist
        DB_URI = 'file:{}?mode=rw'.format(pathname2url(dbfile))
        conn = sqlite3.connect(DB_URI, uri=True)
        cursor = conn.cursor()
        print('Connected to database - ' + dbfile)
        logger.info('Connected to database - ' + dbfile)

    except sqlite3.OperationalError:
        # handle missing database case
        print('No database found. Creating a new one - ' + dbfile)
        logger.info('No database found. Creating a new one - ' + dbfile)
        conn = sqlite3.connect(dbfile)
        cursor = conn.cursor()
        # UNIQUE constraint prevents duplication of data on multiple runs of this script
        # ON CONFLICT FAIL allows us to count how many times this happens
        # ['code', 'direction', 'full_name', 'display_name', 'description', 'is_variable', 'is_green', 'is_tracker', 'is_prepay', 'is_business', 'is_restricted', 'term', 'available_from', 'available_to', 'links', 'brand']
        # Make a CREATE TABLE string...
        makeTable = 'CREATE TABLE dataseries (date TEXT, PVForecast REAL, PVActual REAL, Ratio REAL);'
        #print (makeTable)
        cursor.execute(makeTable)
        conn.commit()
        print('Database created - ' + dbfile)
        logger.info('Database created - ' + dbfile)

    return conn

'''
########################################################################################################

    Main code

########################################################################################################
'''

'''
    Get config data
'''
dbfile = 'PV_Forecast_History.sqlite'
logfile = 'PV_Forecasts_Actuals.log'

config = c.ConfigParser()
config.read('PVForecastActuals.ini')

'''
    Config INI file format:

    [DEFAULT]
    GE_api_token = <token>
    SC_api_token = <token>
    inverterid = <inverter_ID>
    dbfile = databasefile.sqlite
    logfile = PV_Forecasts_Actuals.log

'''

GE_API_token = config['DEFAULT']['GE_api_token']
SC_API_token = config['DEFAULT']['SC_api_token']
dbfile  = config['DEFAULT']['dbfile']
logfile = config['DEFAULT']['logfile']
inverterID = config['DEFAULT']['inverterid']

'''
    Sort logging
'''
# Need to find location of .py script to use that for logfile path!
dir = os.path.dirname(sys.argv[0])
#print ('dir is', dir)
logfile = os.path.join(dir, logfile)
#print ('Log at',logfile)

logging.basicConfig(filename=logfile, level=logging.INFO,
# logging.basicConfig(level=logging.INFO,
    format='%(asctime)s %(name)s:%(levelname)s:%(message)s')

logger = logging.getLogger('PVForecastActuals')

'''
    Parse runtime arguments

    program.py [-v|--verbosity] [--PVOffset n] [--dbNoOp] [--fromFiles --file <file1> [--file <file2>]...] [--actualsOnly]

'''
parser = argparse.ArgumentParser(prog='GetPVForecastActuals')
parser.add_argument("-v", "--verbosity", help="increase output verbosity", action = "store_true")
parser.add_argument("--PVOffset", help="Number of days back for PV Actuals, default 0=today", type=int)
parser.add_argument("--dbNoOp", help="Don't update database; default is update", action = "store_true")
parser.add_argument("--fromFiles", help="Read Forecast data from files; default is from web; requires '--file' option", action = "store_true")
parser.add_argument("--file", help="file to read data from, can be specified multiple times", action = "append")
parser.add_argument("--actualsOnly", help="Don't do Forecast, only do Actuals & Ratio calculate/update", action = "store_true")

args = parser.parse_args()

verbose = args.verbosity    # This doesn't actually do anything yet!
database_NoOp = args.dbNoOp # Don't update the database, only read it
actualsOnly = args.actualsOnly  # Only do Actuals + Ratio, not Forecast (usually cos 429 requests exceeded!!)

PVDayOffset = 0
if args.PVOffset != None:
    if args.PVOffset < 0:
        logger.error('PV Day Offset must be +ve, can only report on today or previous!')
        parser.exit(0,'PV Day Offset must be +ve, can only report on today or previous - exiting\n')
    else:
        PVDayOffset = args.PVOffset

inputFiles = ['SolcastAPI/PVForecastEast_2024-07-01.json','SolcastAPI/PVForecastWest_2024-07-01.json']
fromFiles = args.fromFiles
if fromFiles:
    if args.file == None:
        logger.error('--fromFiles specified with no --file options - exiting')
        parser.exit(0,'No file(s) provided for fromFiles option - exiting\n')
    else:
        inputFiles = args.file
if verbose:
    print("Using params:")
    print("\tdbNoOp:", database_NoOp)
    print("\tPVOffset:", str(PVDayOffset))
    print("\tactualsOnly:", actualsOnly)
    print("\tfromFiles:", fromFiles)
    if fromFiles:
        for f in inputFiles:
            print("\t\t"+f)


'''

   Get the database open...

'''

conn = openDatabase(dbfile)
cursor = conn.cursor()

'''
#################################################################################################################

    Get the forecast, produce a single number from it, and store against the date (Today + 1)

#################################################################################################################
'''

# Work out current ordinal day and the day we want a forecast for
nowDate = datetime.date.today()
fcastDay = nowDate.toordinal() + 1

# Load sets
if not actualsOnly:
    FcastData = []
    if fromFiles:
        print('Loading forecast from files')
        logger.info('Loading forecast from files')
        #east = getFilecast('SolcastAPI/fcastEast_2024-06-02_1400.json')
        #west = getFilecast('SolcastAPI/fcastWest_2024-06-02_1400.json')
        FcastData = getFilecastData(inputFiles)
    else:
        print('Loading forecast from web')
        logger.info('Loading forecast from web')
        FcastUrls = ['https://api.solcast.com.au/rooftop_sites/6105-58b6-fc80-cd65/forecasts?format=json',
                        'https://api.solcast.com.au/rooftop_sites/51a4-1676-62b2-31bf/forecasts?format=json']
        FcastData = getForecast(FcastUrls)

    if len(FcastData) < 1:
        print("No SolCast data returned, exiting")
        logger.error("No SolCast data returned, exiting")
        totalPower = -1
    else:

        totalPower = sumPower (FcastData, fcastDay)

        # We now have forecast for today + 1
        fcastDate = datetime.date.fromordinal(fcastDay) # '2024-06-16'

        print (fcastDay, datetime.date.fromordinal(fcastDay), totalPower)

        if database_NoOp != True:
            insertForecast = "INSERT INTO 'dataseries' (date, PVForecast) VALUES(?,?);"
            cursor.execute(insertForecast, (fcastDate.isoformat(),totalPower))
            conn.commit()

'''

    Collect the GivEnergy PV etc. data for Today  and save that

'''
PVDate = datetime.date.fromordinal(nowDate.toordinal() + PVDayOffset) # If yesterday required
PVData = getPVActuals(PVDate) # Returns PV Actuals for date calculated above
print (PVDate, PVData)

actualDate = PVDate.isoformat()
getForecastStmt = "SELECT PVForecast FROM dataseries WHERE date = ?;"
cursor.execute(getForecastStmt, (actualDate,))
forecast = cursor.fetchone()
if forecast == None:
    # No previous record for this date, so better put one in!
    if database_NoOp != True:
        cursor.execute(insertForecast, (actualDate,None))
        conn.commit()
    forecastVal = None
else:
    forecastVal = forecast[0]

# At this point, we either
#   - have a valid forecastVal
#   - didn't have a previous record, val = None
#   - or the one we had had None
if forecastVal != None:
    ratio = forecastVal/PVData["PV_Total"]
else:
    ratio = None    # Nothing else has meaning, we cant divide by zero!

print(str(forecastVal), str(PVData["PV_Total"]), str(ratio))
if database_NoOp != True:
    updateValues = "UPDATE 'dataseries' SET PVActual = ?, Ratio = ? WHERE date = ?;"
    cursor.execute(updateValues, (PVData["PV_Total"], ratio, actualDate))
    conn.commit()

print("All done!")
logger.info("All done!")
