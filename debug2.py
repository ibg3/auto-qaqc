import datetime

import pandas as pd

import download_dwd
incomeN = '/home/pa.ney/incomingNeutrons_JUNG/income_N_JUNG.txt' #path where to save and name of .txt file

date_start = pd.to_datetime('2020-08-01 00:00:00', format='%Y-%m-%d %H:%M:%S')
date_end = datetime.date.today()
station = '02110' # JUNG = Jungfraujoch; select your reference station: http://www01.nmdb.eu/nest/
resolution = 'hourly' #neutron count aggregation time in minutes, raw resolution usually 1 minute
field= 'moisture'

ret = download_dwd.download(field=field, station=station, resolution=resolution, start=date_start, end=date_end)


print (ret)