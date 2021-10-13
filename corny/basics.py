"""
CoRNy Basics
    General helper functions that make life easier
"""

import pandas as pd
import numpy as np
import os
import dateutil

name_std = '_std'
name_err = '_err'

def debug():
    """
        Sets a marker at this position where the running script stops
        and enters interactive mode for debugging
    """
    import pdb
    pdb.set_trace()

def one_of(a, b, default=np.nan):
    """
    Return a or b or default.
    E.g.: latitude = one_of(lat_column, station_lat)
    """
    if a:
        return(a)
    elif b:
        return(b)
    else:
        return(default)

def safe_cast(var, to_type, default=None):
    """
    Convert variable type (int, float, str, ...) safely.
    Use:
    """
    if default is None:
         if   to_type==float: default = np.nan
         elif to_type==str  : default = ''

    try:
        return(to_type(var))
    except (ValueError, TypeError):
        return(default)


def col_is_unique(s):
    """
    Check whether a pandas column has all identical values.
    Use: if col_is_unique(data.lon): data = data.iloc[0]
    """
    import numpy
    if isinstance(s, numpy.ndarray):
        a = s
    else:
        import shapely
        if isinstance(s[0], shapely.geometry.point.Point):
            a = np.array([pg.x for pg in s])
        else:
            import pandas
            if isinstance(s, pandas.Series):
                a = s.to_numpy()
            else:
                print('! col_is_unique: variable is neither of ndarray, pandas series, shapely point.')

    # Boolean array
    b = a[0] == a
    # Check all
    return(b.all())


def str2dt(s, tz=None):
    """
        str2dt('2021-12-24', tz='UTC')
        = datetime object
        Parses the date time string as a datetime object
    """
    dto = dateutil.parser.parse(s) # uses dateutil
    if tz is None:
        return(dto)
    elif tz == 'UTC':
        return(dto.replace(tzinfo=pytz.UTC))
    else:
        return(dto.replace(tzinfo=tz))

def interpret_time_format(s):
    s = s.replace('monthname', '%b').replace('month', '%M')
    s = s.replace('day', '%d').replace('hour', '%H').replace('year', '%Y')
    s = s.replace('minute', '%M').replace('min', '%M')
    return(s)

def time_resolution(data, unit='sec'):
    """
    Estimate time resolution of pandas in given units.
    """
    tres = data.index.to_series().dropna().diff().median().total_seconds()

    if   unit == 'min':  tres *= 60
    elif unit == 'hour': tres *= 60*60
    elif unit == 'day':  tres *= 60*60*24

    return(tres)


def clean_interval_str(a):
    """
    return valid interval string (1Min, 2H, ...) from user input
    """

    # if number is provided, assume it's in hours
    if a.isdigit(): a = str(a)+'hour'

    # harmonize spelling
    a = a.replace('sec','S').replace('hour','H').replace('min','Min').replace('day','D').replace('week','W').replace('month','M').replace('year','A')

    # remove plural s
    a = a.replace('s','')

    return(a)


def aggregate(data, aggstr, func='mean', set_std=[], adapt_err=[], min_count=None, verbose=False):
    """
        aggregate(data, '1H')
        = pandas
        Aggregation of the whole data set.
        Adds stddev columns for specific columns.
        Adapts error by 1/sqrt(a) for specific columns.
    """

    # Clean aggregation window string
    aggstr = clean_interval_str(aggstr)

    if verbose: print('| Aggregate data to ' + aggstr + ' time steps...', end='')

    # record time resolution
    tres_before = time_resolution(data)

    # Resample
    aggobj = data.resample(aggstr)
    if   func == 'mean':   data = aggobj.mean()
    elif func == 'median': data = aggobj.median()
    elif func == 'sum':    data = aggobj.sum(min_count=min_count)
    else:
        print('! Aggregation method unknown: ' + method)

    # record time resolution
    tres_after = time_resolution(data)

    # factor by which the time resolution is scaled up
    tres_factor = tres_after / tres_before
    tres_factor_err = 1 / np.sqrt( tres_factor )

    if verbose: print(' (data x%0.2f, error x%.02f)' % (tres_factor, tres_factor_err))

    # Errors scale with sqrt(1/tresfactor)
    for column in adapt_err:
        data[column + name_err] *= tres_factor_err

    # Add empirical standard deviation
    for column in set_std:
        data[column + name_std] = aggobj.std()[column]

    return(data)


def minly(data, agg=1, **kwargs):
    aggstr = '%iMin' % agg
    data = aggregate(data, aggstr, **kwargs)
    return(data)

def hourly(data, agg=1, **kwargs):
    aggstr = '%iH' % agg
    data = aggregate(data, aggstr, **kwargs)
    return(data)

def daily(data, agg=1, **kwargs):
    aggstr = '%iD' % agg
    data = aggregate(data, aggstr, **kwargs)
    data.index.freq = 'D'
    return(data)


# Moving average
def moving_avg(D, column, window=1, err=True, std=True, center=True):
    window = int(window)
    suffix = '_mov' #+str(window)
    rollobj = D[column].rolling(window, center=center)
    D[column+suffix]                = rollobj.mean()
    if std: D[column+suffix+'_std'] = rollobj.std()
    if err: D[column+suffix+'_err'] = D[column+'_err'] * 1/np.sqrt(window)
    return(D)



"""
    cut_period(df, '2019-03-14', '2020-03-14')
    cut_period(df, datetime, datetime)
    cut_period(df, shorter_df)
    = df
    Cut period to that of another data frame.
"""
def cut_period_to(D, a, b=None):
    if a is None or a.strip() == '':
        a = D.index.min()
    if b is None or b.strip() == '':
        b = D.index.max()

    # Cut to other DataFrame
    if isinstance(a, pandas.DataFrame):
        return(D.loc[a.index.min():a.index.max()])

    # Strings to parse
    elif isinstance(a, str):
        if a.strip() == 'today':
            a = datetime.now().strftime('%Y-%m-%d')
            b = D.index.max().strftime('%Y-%m-%d %H:%M')

        a = str2dt(a, 'UTC')
        if isinstance(b, str):
            b = str2dt(b, 'UTC')
        print(a,b)
        return(D.loc[a:b])

    # Datetimes
    else:
        return(D.loc[a:b])


"""
    Performance(data[[a,b]]
    = [kge, nse, rmse, correl, var, bias]
    Evaluation of two columns of a df
"""
def Performance(data, title='Test', writeout=True):

    from hydroeval import evaluator, kge, rmse, nse

    columns = data.columns
    D = data.copy().dropna().values
    k = evaluator(kge,  D[:,0], D[:,1]).flatten()
    r = evaluator(rmse, D[:,0], D[:,1])
    n = evaluator(nse,  D[:,0], D[:,1])
    if writeout:
        print('%35s: KGE %.3f, NSE %.3f, RMSE %.3f, Correlation %.3f, Variance %.3f, Bias %.3f' %
            (columns[0]+' vs. '+columns[1], k[0], n[0], r[0], k[1], k[2], k[3]))
    else:
        return([k[0], n[0], r[0], k[1], k[2], k[3]])

def optimize(df, opt, cmp, span=(700,1100), func='kge'):
    if   func=='kge':
        fi = 0
        best = -1
    elif func=='nse':
        fi = 1
        best = -1
    elif func=='rmse':
        fi = 2
        best = 100000
    else: print('! Unknown function. Choose '+'kge, NSE, RMSE')

    best_i = 0
    for i in np.arange(span[0],span[1]):
        df[opt+'_opt'] = df[opt] * i
        p = Performance(df[[opt+'_opt', cmp]], writeout=False)
        if fi == 2:
            if p[fi] < best:
                best = p[fi]
                best_i = i
        else:
            if p[fi] > best:
                best = p[fi]
                best_i = i

    df[opt+'_opt'] = df[opt] * best_i
    print("%5i" % best_i, end='')
    Performance(df[[opt+'_opt', cmp]])


def ifdef(a, b, convert=float):
    if not a:
        return(b)
    else:
        return(convert(a))

def xsplit(s, range=0, type=str):
    """
    Split a string by , and ignore spaces,
    convert to certain data type,
    optionally generate an array of length `range`.
    E.g.: coords = xplit('51.5, 12.1, 120', range=3, type=float)
    """
    if isinstance(s, str):
        s = s.replace(',',' ')
        a = np.array(s.split(), dtype=type)
    else:
        a = np.array([])

    # fill up with NaNs
    for i in np.arange(range-len(a)):
        a = np.append(a, np.nan)
    return(a)

# Split a string by \s,\s into an array
def csplit(s, range=0, type=str):
    s = re.sub(r'\s*,+\s*', ',', s)
    s = re.sub(r',+', ',', s)
    a = np.array(s.split(','), dtype=type)
    return(a)

def chomp(x):
    if x.endswith("\r\n"): return x[:-2]
    if x.endswith("\n") or x.endswith("\r"): return x[:-1]
    return(x)



def read_files(pattern, index_col=1, skiprows=14):
    from glob import glob
    D = None
    for f in glob(pattern):
        Dx = pandas.read_csv(f, index_col=index_col, parse_dates=True, infer_datetime_format=True,
                             skipinitialspace=True, sep=',', skiprows=skiprows, encoding="cp850",
                       names=['RecordNum','t','#ClkTicks','PTB110_mb','P4_mb','P1_mb','Vbat','T1_C','RH1',
                              'N1Cts','N2Cts','N1ETsec','N2ETsec','N1T(C)','N1RH','N2T(C)','N2RH','T_CS215','RH_CS215',
                              'GpsUTC','LatDec','LongDec','Alt','Qual','NumSats','HDOP',
                              'Speed_kmh','COG','SpeedQuality','strDate'])
        if D is None:
            D = Dx.copy()
        else:
            D = pandas.concat([D, Dx])
    return(D)
    #D.head(10)

#######################################
#   Files in/out                      #
#######################################


def file_save_msg(file, name='File', end=''):
    size = os.stat(file).st_size
    if   size < 1024:    sizestr = "%.0f Bytes" % (size)
    elif size < 1024**2: sizestr = "%.0f KB"    % (size/1024)
    else:                sizestr = "%.1f MB"    % (size/1024/1024)
    print(cprintf("< %s saved to %s (%s)" % (name, file, sizestr), 'green'), end=end)


def ftp_is_file(FTP, object):
    """
    check if remote object is file
    """
    if FTP.nlst(object) == [object]:
        return True
    else:
        return False


def download(archive_file='', source='FTP', server=None, user=None, pswd=None,
             ftp_prefix='', ftp_suffix='', sd_path='', sd_prefix='', sd_suffix='',
             update_all=False):

    # if a folder was given
    if not archive_file.endswith('zip'):
        archive_file = os.path.join(archive_file,'') + 'archive.zip'

    # Check what has already been downloaded
    dirname = os.path.dirname(archive_file)
    if dirname != '' and not os.path.isdir(dirname):
        os.makedirs(dirname)
    archive = zipfile.ZipFile(archive_file, 'a', zipfile.ZIP_DEFLATED)
    archive_list = archive.namelist()
    archive_size = os.stat(archive_file).st_size /1024/1024
    print("i %5s files were already downloaded (%.2f MB)." % (len(archive_list), archive_size))

    local_files = pandas.DataFrame()
    local_files['name'] = archive_list
    local_files['size'] = [archive.getinfo(file).file_size for file in archive_list]

    if source=='FTP':
        # Select new files from FTP
        import ftplib
        try:
            remote = ftplib.FTP(server)
            print('| FTP connection OK', end='')
            remote.login(user, pswd)
            print(', login OK', end='')
            if '/' in ftp_prefix:
                folder = ftp_prefix[0:ftp_prefix.rindex('/')]
                ftp_prefix = ftp_prefix[ftp_prefix.rindex('/')+1:len(ftp_prefix)]
                remote.cwd(folder)
                print(', folder: '+folder, end='')

            print(', looking for: %s*' % ftp_prefix)
            remote_list = list(filter(lambda item: item.startswith(ftp_prefix) and ftp_is_file(remote, item), remote.nlst()))
            print("i %5s files found on the FTP server." % len(remote_list))
            remote_files = pandas.DataFrame()
            remote_files['name'] = remote_list
            remote_files['size'] = [remote.size(file) for file in remote_list]

        except ftplib.all_errors as e:
            print(cprintf("\n"+'! FTP connection error: %s' % e, 'red'))
            exit()

    elif source=='SD':
        # Select new files from SD-Card
        #remote_list = list(filter(lambda item: item.endswith(suffix=''), os.listdir(sd_path)))
        remote_list = [os.path.basename(x) for x in glob(sd_path+'/'+sd_prefix+'*'+sd_suffix)]
        print("i %5s files found on the SD backup." % len(remote_list))
        remote_files = pandas.DataFrame()
        remote_files['name'] = remote_list
        remote_files['size'] = [os.stat(sd_path+'/'+file).st_size for file in remote_list]


    elif source=='DMP':
        # Select new files from DMP
        remote_list = [os.path.basename(x) for x in glob(sd_path+'/'+sd_prefix+'*'+sd_suffix)]
        print("i %5s files found on the SD backup." % len(remote_list))


    else:
        return

    if update_all:
        update_list = remote_list
    else:
        #update_list = list(filter(lambda item: not item in archive_list, remote_list))
        merged_files = pandas.merge(local_files, remote_files, how='right', on='name')
        new_files = merged_files[merged_files.size_x != merged_files.size_y]
        update_list = np.unique(new_files.name.values).tolist()
        #print(merged_files)
        #print(update_list)

    print("i %5s new files selected for download." % len(update_list))

    if len(update_list) == 0: return

    # Download files and add to Zip
    from io import BytesIO
    i = 0
    for filename in update_list:
        i += 1
        #print("|  Archiving files %5s/%s: %s" % (i, len(update_list), filename))
        progressbar(i-1, len(update_list), title='Archiving', prefix=filename)

        if source=='FTP':
            memory = BytesIO()
            remote.retrbinary("RETR " + filename, memory.write) # FTP->memory
            archive.writestr(filename, memory.getvalue())    # memory->archive

        elif source=='SD':
            archive.write(os.path.join(sd_path,'') + filename, filename)

    progressbar(i-1, len(update_list), title='Archiving', prefix=filename, end=True)

    archive.close()
    if source=='FTP': remote.close()
    file_save_msg(archive_file, "Archive", end="\n")



import re
re_dataselect = re.compile(r'//DataSelect\s*=\s*(\w+)')
re_columns = re.compile(r'/+(RecordNum.+)')
re_columns2 = re.compile(r'/+(GpsUTC.+)')
re_crnsdata = re.compile(r'^\d+')

def read(filename, archive=None, tz='UTC', path='', skip=0):

    header_skip = 0
    datastr = ''
    with archive.open(filename,'r') if archive else open(path+filename, encoding="cp850") as file:
        for _ in range(skip):
            next(file)

        for line in file:
            if isinstance(line, bytes):
                line = line.decode(errors='ignore')
            if re_crnsdata.search(line):
                datastr += line

    return(datastr+"\n")


def read_header(filename, archive=None, path=''):

    import re
    import os
    re_crnsdata = re.compile(r'^\d+\,')
    re_strangecoord = re.compile(r'\d,[EW],')
    re_columns = re.compile(r'/+(RecordNum.+)')
    re_columns2 = re.compile(r'/+(GpsUTC.+)')
    strange_coords = []
    data_columns = ''
    col_row_detected=False
    with archive.open(filename,'r') if archive else open(path+filename) as file:
        for line in file:
            if isinstance(line, bytes):
                line = line.decode(errors='ignore')

            if re_crnsdata.search(line):
                # get column number of strange direction
                strange_coords = [line.count(',', 0, m.start())+1 for m in re_strangecoord.finditer(line)]
                if strange_coords:
                    #print(line)
                    break
            else:
                match_columns = re_columns.search(line)
                if match_columns:
                    data_columns = match_columns.group(1)
                    col_row_detected=True
                    continue
                match_columns2 = re_columns2.search(line)
                if match_columns2:
                    data_columns += ',' + match_columns2.group(1)
                    continue

    if len(data_columns)<=0:
        print('! Input file contains no headers (e.g., //RecordNum...). Try to define input_columns in the config file.')
        return(None)
    else:
        data_columns = chomp(data_columns)
        data_columns = csplit(data_columns)
        #re.sub(r'\s*,+\s*', ',', data_columns)
        #data_columns = re.sub(r',+', ',', data_columns)
        #data_columns = data_columns.split(',')
        if strange_coords:
            print("\n!  "+'Found strange coordinate format and missing columns, trying to fix it...', end='')
            new_columns = ['NS','EW'] # Assuming that northing is first, easting is second.
            for pos in strange_coords:
                data_columns.insert(pos, new_columns.pop(0))
        #if the first row of col names was missing we manually add
        if not col_row_detected:
            print('Manually add half of column names')
            data_column_row=np.array(('RecordNum','Date Time(UTC)',
                                      'PTB110_mb','P4_mb','P1_mb','Vbat',
                                      'T1_C','RH1','N1Cts','N2Cts','N1ETsec',
                                      'N2ETsec','N1T(C)','N1RH','N2T(C)',
                                      'N2RH','T_CS215','RH_CS215'))
            #append together
            data_columns=np.append(data_column_row,data_columns[1:])
        return(data_columns)


def read_file(filename, archive=None, tz='UTC'):
    header_skip = 0
    datastr = ''
    with archive.open(filename,'r') if archive else open(filename, encoding="cp850") as file:
        for line in file:
            if isinstance(line, bytes):
                line = line.decode(errors='ignore')
            if re_crnsdata.search(line):
                datastr += line
    return(datastr+"\n")

import io
import os
import zipfile

def read_and_convert(path, prefix='', suffix='', data_columns=[], progress='file'):

    archive = None
    files = []

    if path.endswith('.zip'):
        archive = zipfile.ZipFile(path, 'r')
        files = [x for x in archive.namelist() if x.endswith(suffix) and x.startswith(prefix)]

    elif os.path.isdir(path):
        pattern = path + prefix +'*'+ suffix
        files = glob(pattern)
        if len(files)==0:
            print("ERROR: Folder is empty: " + pattern)
            return(None)
    else:
        print("ERROR: Input is neither a file, folder, nor a zip archive.")
        return(None)

    datastr = ''
    i = 0
    last_progress = 0 # in %
    i_max = len(files)

    for filename in files:
        i += 1

        if progress == 'percent':
            this_progress = (i+0.01)/len(files)//0.1*10 # in %, offset 0.01 because x/x//0.1 is 9
            if this_progress > last_progress:
                print("%.0f%% " % this_progress, end='')
                last_progress = this_progress

        elif progress == 'file':
            print('%5d/%d: %s' % (i, i_max, filename))

        if datastr=='':
            #if data_columns == []:
            #    data_columns = read_header(filename, archive)
            datastr = read_file(filename, archive)
        else:
            datastr += read_file(filename, archive) #data.append() #, verify_integrity=True)

    if not archive is None:
        archive.close()

    #DEBUG output raw data file
    #with open('temp.txt','a') as f:
    #    f.write(datastr)

    data = make_pandas(datastr, data_columns)
    if data is None:
        print('Error: Cannot interprete the data. Check the column header, is this correct? '+ ','.join(data_columns))
        return()
    else:
        return(data)

def make_pandas_old(datastr, file=False, columns=None, header_skip=0, index=1):
    if file:
        f = datastr
    else:
        f = io.StringIO(datastr)

    try:
        data = pandas.read_csv(f, index_col=index, parse_dates=True, infer_datetime_format=True, skipinitialspace=True,
                               sep=',', skiprows=12, encoding="cp850", error_bad_lines=False, warn_bad_lines=False, names=columns, dtype=object)
    except Exception as e:
        print("ERROR interpreting data format: "+str(e))
        return(None)

    data = data.apply(pandas.to_numeric, errors='coerce')
    return(data)

def make_pandas(datastr, columns=None, header_skip=0, index=1, sep=',', timestamp=False):

    try:
        data = pd.read_csv(io.StringIO(datastr), encoding='cp850', skipinitialspace=True,
                            sep=sep,  skiprows=header_skip, names=columns,
                            error_bad_lines=False, warn_bad_lines=False,
        # Depreciated: no longer convert columns directly on input:
        # parse_dates=True, infer_datetime_format=True, index_col=index, dtype = dtypes
        # dtypes = { c : float for c in columns }; dtypes[columns[index]] = str
                            dtype=object)
    except Exception as e:
        print("! ERROR interpreting data format: "+str(e))
        return(None)

    #print(data.head(3))
    # Tidy up
    data = data.loc[data.index.dropna()]
    len1 = len(data)

    ## Convert time column to a valid DateTime object
    if isinstance(index, list):
        if len(index) == 2:
            index_column = '_time'
            #TODO: check if index out of bounds
            data[index_column] = pd.to_datetime(data.iloc[:,index[0]] +' '+ data.iloc[:,index[1]], errors='coerce')
        else:
            print(index)
    else:
        index_column = columns[index]
        if timestamp:
            data[index_column] = pd.to_datetime(data[columns[index]], errors='coerce', unit='s')
        else:
            data[index_column] = pd.to_datetime(data[columns[index]], errors='coerce')

    #print(data.head(3))
    ## drop any failures
    data = data.dropna(subset=[index_column])
    ## Set the DateTime column as index
    data.set_index(index_column, inplace=True)
    ## Convert all the regular columns to numeric and drop any failures
    data = data.apply(pd.to_numeric, errors='coerce')

    ## Sort and unify the index and set the time zone as UTC
    data = data.sort_index().drop_duplicates().tz_localize('UTC')

    #print(data.head(3))
    #print(data.index.dtype)

    len2 = len(data)
    if len2 < len1: print("i   Dropped %i malformed lines." % (len1-len2))

    ## Find out which column names are null
    bad_columns = []
    for c in range(len(columns)):
        if pd.isnull(columns[c]):
            bad_columns.append(c)
    ## Reassign data using only non-bad columns
    data = data.iloc[:, [i for i,n in enumerate(data.columns) if i not in bad_columns]]

    #print(data.head(3))
    return(data)



def read_corny(file):
    data = pandas.read_csv(file, index_col=0, parse_dates=True, infer_datetime_format=True, skipinitialspace=True,
                           sep=',', encoding="cp850", error_bad_lines=False, warn_bad_lines=False) #, dtype=object)
    print("%i lines, %i columns: %s" % (len(data), len(data.columns), ', '.join(data.columns)))
    return(data)

read_cornish = read_corny

def read_geojson(file, columns=['label','short','type','lat','lon']):
    import geojson
    with open(file) as f:
        gj = geojson.load(f)

    # Run through geojson and fill a Sensor DataFrame
    D = pandas.DataFrame([], columns=columns)
    for i in range(len(gj['features'])):
        Dx = pandas.DataFrame([[
            gj['features'][i]["properties"]['Id'],
            gj['features'][i]["properties"]['short'],
            gj['features'][i]["properties"]['Inst'],
            gj['features'][i]["geometry"]["coordinates"][1],
            gj['features'][i]["geometry"]["coordinates"][0]]],
            columns=columns)
        D = D.append(Dx)
    D = D.sort_values('label')
    D['color'] = 'black'
    D = D.set_index(np.arange(1,len(D)+1))
    return(D)



def report_size(file, verb='Saved', unit='MB'):
    import os
    if unit=='KB':
        factor = 1/1024
    elif unit=='MB':
        factor = 1/1024/1024
    else:
        factor = 1
        unit = 'unknown'
    size = os.stat(file).st_size * factor
    print("%s %s (%.1f %s)." % (verb, file, size, unit))

# Spatial calculations

def latlon2utm(lats, lons):
    import pyproj
    if isinstance(lats, pandas.DataFrame) or isinstance(lats, pandas.Series):
        lats = lats.values
        lons = lons.values

    ## Deprecated:
    # import pyproj
    # utmy, utmx = pyproj.transform(pyproj.Proj("epsg:4326"), pyproj.Proj("epsg:31468"), lats, lons)
    ## New pyproj2 syntax:
    from pyproj import Transformer
    utmy, utmx = Transformer.from_crs("epsg:4326", "epsg:31468").transform(lats, lons)

    return(utmy, utmx)

def utm2latlon(utmx, utmy):
    import pyproj
    if isinstance(utmx, pandas.DataFrame) or isinstance(utmx, pandas.Series):
        utmx = utmx.values
        utmy = utmy.values

    ## Deprecated:
    # import pyproj
    # lats, lons = pyproj.transform(pyproj.Proj("epsg:31468"), pyproj.Proj("epsg:4326"), utmy, utmx)
    ## New pyproj2 syntax:
    from pyproj import Transformer
    lats, lons = Transformer.from_crs("epsg:31468", "epsg:4326").transform(utmy, utmx)

    return(lats, lons)


def fineround(x, reso=3, fine=1):
    # A rounding function that can round to values even in between digits
    # e.g. use fine=1 to round to the nearest .0 (standard digit round)
    #          fine=2 to round to the nearest .0 or .5
    #          ...

    return(np.round(x*fine, int(reso))/fine)


#######################################
#   Spatial Geoanalysis               #
#######################################


#JJ recalculate strange coordinates to proper decimals
# argument is a pandas.DataFrame(columns=[number, direction])
# remember that C.iloc[:,i] is the i^th column of C

def deg100min2dec(C):
    # Convert
    x = C.iloc[:,0] / 100
    deg = np.floor(x)
    dec = deg + (x - deg)/0.6
    # Negate if cardinal direction is south or west
    dec *= C.iloc[:,1].map({'N': 1, 'S': -1, 'E': 1, 'W': -1})
    return(dec)


#JJ use x nearest neighbors for averaging
## find k closest lat/lon to every lat/lon coordinates
def distance(pointA, pointB):
    return sqrt((pointB[0] - pointA[0]) ** 2 + (pointB[1] - pointA[1]) ** 2)

import zipfile
import os


def distanceinkm(xstand,ystand,xfor,yfor): # approximate radius of earth in km

    R = 6373.0
    lat1 = radians(xstand)
    lon1 = radians(ystand)
    lat2 = radians(xfor)
    lon2 = radians(yfor)

    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return(distance)

def Neighbours(lat, lon, numpoints, data):
    numpoints = numpoints+1 # points itself included - therefore add one to get desired output
    points = np.vstack((lat, lon)).T # create numpy array from coordinates

    kdt = KDTree(points, leaf_size=30, metric='euclidean') # build tree with euclidean distances
    neighborpoints = kdt.query(points, k=numpoints, return_distance=False) # find the closest k points

    # calculate maximal distance within the k clostest coordinates
    neighbordist = []
    for i in range(len(points)):
        furthest = np.array(nlargest(1, points[neighborpoints[i]], lambda p : distance(p, (points[i])))) # find the coordinates for the k closest points
        neighbordist.append(distanceinkm(points[i][0],points[i][1], furthest[0][0],furthest[0][1])*1000)

    return neighbordist, neighborpoints

    #neighborpoints = [] # create empty list for all results

    #for i in range(len(points)): ## iterate for all points
    #    nearest = np.array(nsmallest(numpoints, points, lambda p : distance(p, (points[i])))) # find the coordinates for the k closest points
    #    print(nearest)
    #    index = [] # create empty list for the index of the positions

    #    for m in range(len(nearest)):
    #        idx, rest = np.where(points==nearest[m]) # find the rows of these closest k coordinates
    #        idx = stats.mode(idx) # calculate the mode - necessary because sometimes several outputs from above
    #        index.append(idx.mode.tolist()) # create list from the k rows found

    #    neighborpoints.append(index) # create list of k closest locations for all locations
    #for i in range(len(neighborpoints)):
    #    neighborpoints[i] = list(itertools.chain(*neighborpoints[i])) # reduce for one nested list


#######################################
#   Console                           #
#######################################


def report(data, column, meanof=None, correction='', units='', format='i %s'):
    if meanof is None: meanof = column
    evallist = [column] + [data[c].mean() for c in meanof] + [units]
    s = format % tuple(evallist)
    if correction != '':
        if isinstance(correction, list):
            q = 1
            for c in correction:
                q *= data[c]
        elif correction in data.columns:
            q = data[correction]
        s += ' (%+.0f%%)' % (100*(1-q.mean()))
    print(cprintf(s, 'cyan'))

def report_mmsm(data):
    print("%15s %.2f ... %.2f +/- %.2f ... %.2f" % (data.name, data.min(), data.mean(), data.std(), data.max()))

def cprintf(s, fmt=''):
    os.system("") # makes it work also in the Win10 Console
    a = ''
    if fmt=='black':     a='\033[30m'
    if fmt=='red':       a='\033[31m'
    if fmt=='green':     a='\033[32m'
    if fmt=='yellow':    a='\033[33m'
    if fmt=='blue':      a='\033[34m'
    if fmt=='magenta':   a='\033[35m'
    if fmt=='cyan':      a='\033[36m'
    if fmt=='white':     a='\033[37m'
    if fmt=='underline': a='\033[4m'
    return(a + s + '\033[0m')

def progressbar(index, total, length=None, title='Please wait', prefix='', end=False):
    import shutil
    if length is None:
        length = shutil.get_terminal_size()[0]-79
    percent_done = round((index+1)/total*100, 1)
    done = round(percent_done/(100/length))
    togo = length-done

    done_str = '>' * int(done) # '�'
    togo_str = ' ' * int(togo)

    if end: prefix = ' '*60

    print('| %-11s %s%s %3.0f%% %s' % (title, done_str, togo_str, percent_done, prefix), end='\r')
    sys.stdout.flush()

    #if end: print('')
