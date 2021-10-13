clisos_config = '''[getObservation]
offering = Public
resultmodel = om:Observation
stations = RU_C_004
parameter = NeutronCount_Epithermal_Cum1hr,AirHumidity_Relative,AirPressure_2m,AirTemperature
starttime = 2021-09-30T13:44:52
endtime = 2016-01-01T13:44:52

[connection]
host = ibg3wradar.ibg.kfa-juelich.de
port = 8080
url = /eifelrur_public/sos'''
startdate = ''
for line in clisos_config.splitlines():
    if 'starttime' in line:
        startdate = line.split('=')[1].strip()

from dwdweather import DwdWeather
from datetime import datetime


# create client
dw = DwdWeather(category_names='moisture pressure')

# The hour you're interested in.
# The example is 2014-03-22 12:00 (UTC).
query_hour = datetime.strptime(startdate, '%Y-%m-%dT%H:%M:%S')

result = dw.query(station_id=2110, timestamp=query_hour)
print(result)

