
"""
CoRNy exdata.NM
    Get Data from NMDB
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import pytz
import requests
import re
from configparser import ConfigParser

from .basics import cprintf, file_save_msg, str2dt

# Neutron monitor class
class NM:

    # X = NM()
    def __init__(self, station=None, resolution=None, file=None, config=None, path='.', verbose=False):
        
        self.verbose = verbose
        self.data = None
        self.most_recent = False
        self._internet_error = False
        
        if config is None:
            #self.__config_file = os.path.join(os.path.dirname(__file__), 'config/config.cfg')
            #if self.verbose: print(cprintf('> Reading NM config: ' + self.__config_file, 'yellow'))
            #self.config = configparser.ConfigParser()   
            #temp = self.config.read(self.__config_file)
            self.config = ConfigParser()
            self.config['correction'] = {'NM_path': path, 'NM_station': station, 'NM_resolution': resolution}
        else:
            self.config = config
        
        # Setup data directory
        if self.config:
            if not os.path.exists(self.config['correction']['NM_path']):
                os.makedirs(self.config['correction']['NM_path'])
        
        if station is None:
            self.station = self.config['correction']['NM_station']
        else:
            self.station = station
            
        if resolution is None:
            self.resolution = self.config['correction']['NM_resolution']
        else:
            self.resolution = resolution
        
        if self.resolution == '1day':
            self.resolution_min = 1440
        elif self.resolution == '1hour':
            self.resolution_min = 60
        elif self.resolution == '10min':
            self.resolution_min = 10
        elif self.resolution == '1min':
            self.resolution_min = 1
        
        self.file = file
        #self.file = _filename(datetime.now().strftime('%Y%m%d%H%M%S'))

            
    def _filename(self, string=''):
        if string: string = '-' + str(string)
        return("%s%s-%s%s.dat" \
            % (self.config['correction']['NM_path'], self.station, self.resolution, string))
        
            
    def get(self, start=None, end=None):
        if end is None:
            end = datetime.now()
            self.most_recent = True
        
        # If the user set a filename, just read from it
        if not self.file is None:
            self._reader(file)
            self.data = self.data.tz_localize('UTC')
            return(self)
        
        if start is None:
            print('! I do not know which date to look up, please provide a start date.')
            return(self)
        
        now = datetime.now(tz=pytz.UTC) ##datetime.datetime.utcnow().date(),
        end_request = end ###
        
        # Read data
        data = []
        if self.resolution in ['1day', '1hour']:
        
            # Go through all years...
            for y in range(end.year - start.year +1):
            
                # For daily resolution, it is almost no extra cost to download from Jan 1st to Dec 31th
                y_start = datetime(year=start.year+y, month= 1, day= 1, tzinfo=pytz.UTC)
                y_end   = datetime(year=start.year+y, month=12, day=31, hour=23, minute=59, tzinfo=pytz.UTC)
            
                # if y_end is in the future, only then cut to the end of the requested data
                if y_end > now:
                    data.append( self._read( y_start,   end, self._filename(start.year+y)))
                else:
                    data.append( self._read( y_start, y_end, self._filename(start.year+y)))
            
#        elif self.resolution == '1hour':
#            for y in range(end.year - start.year +1):
                # YY-Jan-01 to today
#                data.append(self._read(datetime(year=start.year+y, month=1, day=1, tzinfo=pytz.UTC),
#                                       datetime(year=start.year+y, month=12, day=31, hour=23, minute=59, tzinfo=pytz.UTC),
#                                       self._filename(start.year+y)))
        
        elif self.resolution == '10min':
        
            # Go through all days
            delta = end - start
            for d in [start + relativedelta(months=+m) for m in range(0, delta.days//12+1)]:
            
                # For minly resolution, it is almost no extra cost to download from 00:00 to 23:59
                d_start = d.replace(day=1, hour=0, minute=0)
                d_end   = d.replace(day=1, hour=23, minute=59, second=0) + relativedelta(months=+1) - timedelta(days=1) 
                
                # if d_end is in the future, only then cut to the end of the requested data
                if y_end > now:
                    data.append( self._read( y_start,   end, self._filename(d.strftime('%Y%m'))))
                else:
                    data.append( self._read( y_start, y_end, self._filename(d.strftime('%Y%m'))))
                    
                #data.append(self._read(,self._filename()))
        
        elif self.resolution == '1min':
            delta = end - start
            for d in [start + timedelta(days=d) for d in range(0, delta.days+2)]:
                data.append(self._read(d.replace(hour=0, minute=0), d.replace(hour=23, minute=59, second=0), self._filename(d.strftime('%Y%m%d'))))
        
        if self._internet_error == True:
            self.data = 1
        else:
            self.data = pd.concat(data)
        #print("Available NM data from: %s to %s" % (self.data.index.min().strftime('%Y-%m-%d %H:%M'), self.data.index.max().strftime('%Y-%m-%d %H:%M')))
        return(self)
    
    # Read existing file or download
    def _read(self, start, end, file):

        #print("\n_read:", start,end,file)
        is_tz_aware = start.tzinfo is not None and start.tzinfo.utcoffset(start) is not None
        if os.path.exists(file):
            
            data = self._reader(file, localize=is_tz_aware)
            
            # 
            now = datetime.now(pytz.utc)
            #if end > now:
            #    end = now #self.most_recent = True 
            #TODO BAD FIX# 
            #self.most_recent = True 
            
            # Looking for a future date?
            if start > now:
                return(None)
            
            #  + timedelta(hours=1)
            # NM data already covers CRNS period?
            elif data.index.min() <= start and (data.index.max() + timedelta(minutes=self.resolution_min) >= end): # or self.most_recent):
                #if not is_tz_aware:
                #    data = data.tz_localize('UTC')
                return(data)
            else:
                print("\ni Local NM period is not covering the requested period.")
                if len(data) == 0:
                    print("i   NM data is empty.")
                else:
                    print("i   NM data from: %s to %s" % (data.index.min().strftime('%Y-%m-%d %H:%M'), data.index.max().strftime('%Y-%m-%d %H:%M')))
                print("i Requested from: %s to %s" % (start.strftime('%Y-%m-%d %H:%M'), end.strftime('%Y-%m-%d %H:%M')))
        
        downloaded = self._download(start, end, file)
        if downloaded is None:
            return(None)
        else:
            return(self._reader(file))
            
                
    def _reader(self, file, localize=True):
        print('.', end='')
        data = pd.read_csv(file, index_col=0, header=None, sep=";", names=['time','NM'],
                           parse_dates=True, infer_datetime_format=True)
        if localize: 
            data = data.tz_localize('UTC')
            
        #print(data.index.dtype)
        return(data)
        
    def download(self, start, end=None, file=None, force=True, headline=True):
        
        if end is None:
            end = datetime.now()
        
        if file is None:
            if not self.file is None:
                file = self.file
            else:
                file = self.station + '.csv'
        self.file = file
        
        if isinstance(start, str):
            start = str2dt(start)
        if isinstance(end, str):
            end = str2dt(end)
            
        return(self._download(start=start, end=end, file=file, force=force, headline=headline))
            
    def _download(self, start, end, file, force=True, headline=False):
    
        force_str = '&force=1' if force else ''
        url = "http://www.nmdb.eu/nest/draw_graph.php?wget=1&stations[]=%s&tabchoice=revori&dtype=corr_for_efficiency&tresolution=%i%s&date_choice=bydate&start_year=%s&start_month=%s&start_day=%s&start_hour=%s&start_min=%s&end_year=%s&end_month=%s&end_day=%s&end_hour=%s&end_min=%s&yunits=0" \
            % (self.station, self.resolution_min, force_str,
            start.strftime('%Y'), start.strftime('%m'), start.strftime('%d'), start.strftime('%H'), start.strftime('%M'),
            end.strftime('%Y'), end.strftime('%m'), end.strftime('%d'), end.strftime('%H'), end.strftime('%M'))
        if self.verbose: print('i Request URL: ' + url)
            
        print("\n|  Downloading incoming cosmic-ray data from nmdb.eu/... ")
        try:
            r = requests.get(url)
        except:
            print(cprintf('! Internet connection failed. Skipping i-correction...','red'))
            self._internet_error = True
            return(None)
            
        if self.verbose: print('i received %s chars... ' % len(r.text), end='')
        # if date has not been covered we raise an error
        if str(r.text)[4:9]=='Sorry':
            raise ValueError('Request date is not avalaible at ',self.station, ' station, try other Neutron Monitoring station')
        # Write into file
        re_data_line = re.compile(r'^\d')
        with open(file, 'w') as f:
            if headline:
                f.write("Date_Time; N_Cts\n")
            for line in r.text.splitlines():
                if re_data_line.search(line):
                    f.write(line + "\n")
                    
        file_save_msg(file, '', "\n")

        self.data = pd.read_csv(file, index_col=0, parse_dates=True, sep=';', skipinitialspace=True).tz_localize('UTC')

        return(self)
    
    def to_pickle(self, file=None, sep=';'):
        # Convert NM.csv to Pickle
        if file is None:
            file = self.file
            
        newfile = file[0:file.rindex('.')]+'.pkl'
        self.data.to_pickle(newfile)
        
        file_save_msg(newfile, '', "\n")
        

    