#Setup path for scripts in test module
import os, sys
import pandas as pd
sys.path.append(os.path.join(sys.path[0],'../python'))

import eventGenerator

LOG_FILE = 'src/data/city_log_1.log'
HOSPITAL_FILE = 'src/data/hospitals.csv'

hospitals_data = pd.read_csv(HOSPITAL_FILE, usecols=['latitude','longitude']).dropna()
hospitals_data.columns=['lat','lon']

log_file = ''
with open(LOG_FILE,'r') as f:
    log_file += f.read() + '\n' # add trailing new line character
log_file = log_file.rstrip("\n") # Remove last trailing breakline

print(log_file)
eventGenerator.getEventsFromLogFile(log_file, hospitals_data)