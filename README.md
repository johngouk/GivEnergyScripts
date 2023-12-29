# GivEnergyScripts
Some Python scripts for performing GivEnergy Inverter queries and operations, using the Portal API.
Check out https://givenergy.cloud/docs/api/v1 for how to use the API - you'll need an API Token as described there, and the ID of your Inverter.

They all use an INI file to set up the required API key and Inverter ID.

- **GivEnergyConfig.ini:** config file for all scripts; contains API Token and Inverter ID
- **GivEnergyEcoModeSet.py:** script to set the ECO setting to ON/OFF
- **GivEnergyGetSetSetting.py:** script to get a specified value and set it to another - **INCOMPLETE!!** Uses output file from GivEnergyInverterSettingsRead.py to validate entries 
- **GivEnergyInverterSettingValues.py:** gets all the current values for available settings and saves them in a dated CSV file
- **GivEnergyInverterSettingsRead.py:** get the all available settings and their validation rules, saves to a CSV file inverterSettingsValidation.csv, which is then used as configuration input to the GivEnergyGetSetSetting.py script.
