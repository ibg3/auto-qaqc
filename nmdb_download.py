# -*- coding: utf-8 -*-
"""
Created on Mon Feb 15 17:43:14 2021

@author: pa.ney
"""
# imports ---------------------------------------------------------------------

# import from python
import io
import zipfile

import pandas as pd
import requests
from datetime import datetime

# user constants -------------------------------------------------------------



def getTimeUrl(timestamp):

    # cache miss
    age = (datetime.utcnow() - timestamp).total_seconds() / 86400
    if age < 1:
        return 'current'
        return (True, False, False)
    elif age < 360:
        return 'current'
        return (False,True,False)
    elif age >= 360 and age <= 370:
        return 'historical'
        return (False,True,True)
    else:
        return 'historical'
        return (False, False, True)


def download_extract_zip(url):
    """
    Download a ZIP file and extract its contents in memory
    yields (filename, file-like object) pairs
    """
    response = requests.get(url)
    with zipfile.ZipFile(io.BytesIO(response.content)) as thezip:
        for zipinfo in thezip.infolist():
            with thezip.open(zipinfo,mode='r') as thefile:
                yield zipinfo.filename, thefile


def download(station, field,resolution, start, end):



    url = "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/%s/%s/%s/" % (resolution, field, getTimeUrl(start) )
    r = requests.get(url)
    print('Request URL: ' + url)

    file_url = ''
    for line in r.text.splitlines():
        if ('_' + station + '_') in line:
            file_url = line.split('href=')[1].split('"')[1]
            break

    url = url + "/" + file_url

    file=None
    data=""
    for (info, f) in download_extract_zip(url):
        if 'Metadaten' not in info:
            for line in f:
                data += (str(line).replace('b\'','')[0:-5].strip()) + '\n'





    return data

