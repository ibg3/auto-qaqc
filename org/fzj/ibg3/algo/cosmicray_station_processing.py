from io import StringIO

import download_dwd

dwd_map = {
    'RU_C_004': '02110',
    'RU_C_005': '02497',
    'RU_C_006': '15000',
}



def execute(msg):

    #!/usr/bin/env python
    # coding: utf-8

    # In[12]:
    # load CRNS data (find header)
    tmp = ""
    for line in msg['orig_data'].splitlines():
        if line.startswith('#'):
            tmp += line[1:]+'\n'
        else:
            tmp += line+'\n'
    data = StringIO(tmp)



    # Get rid of FutureWarnings in Python 3.9.7*
    import warnings


    warnings.simplefilter(action='ignore', category=FutureWarning)

    # load data, resample and create reference information from calibration data
    # add a plot overview of all locations ith the total weighted, the raw data and the simple mean
    # add a timeline plot of all stations
    # add the sm timeseries of all stations

    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np
    import os
    import re
    from scipy.optimize import minimize
    from scipy.optimize import curve_fit
    #from sklearn.linear_model import LinearRegression


    # In[5]:


    # Parts from CoRNy, should be updated regularly: https://git.ufz.de/CRNS/cornish_pasdy
    import corny





    ########### script for vertical and horizontal weighting ############
    #exec(open(r'CR_Weight_Reference_Integrals_new.py').read()) #  open weighting class
    #exec(open(r'Footprint_metrics.py').read()) #  open weighting class

    # define linear function for estimating local pressure, humidity and temperature from ERA5
    def linearfunc(x, a, b):
        return a*x+b

    # define function to otimise N0 from several dates for RMSE
    ################################################################################################################
    a0 = 0.0808; a1 = 0.372; a2 = 0.115  # Desilets 2010

    def RMSE_N0(n0):
        SM = (a0 * (1 / (N / n0 - a1)) - (a2))  # calculate SM from Neutrons and N0
        return np.nanmean(((SM - SM_ref) ** 2))**.5  # return RMSE

    # define function to obtain uncertainty in sm
    def Taylor(N_error, N, N0, bd):
        return N_error*(a0*N0/(N-a1*N0)**4)*((N-a1*N0)**4+8*N_error**2*(N-a1*N0)**2+15*N_error**4)**.5*bd

    p0 = -a2; p1 = a1*a2/(a0+a1*a2) # Köhli et al., 2021
    def RMSE_Nmax(Nmax):
        SM = p0*((1-N/Nmax)/(p1-N/Nmax))
        return np.nanmean(((SM - SM_ref) ** 2))**.5  # return RMSE

    def obtain_Nmax(N, SM_ref):
        Nmax = (-N*p0+N*SM_ref)/(p1*SM_ref-p0)
        return(Nmax)

    def obtain_N0(N, SM_ref):
        N0 = N/(a0/(SM_ref+a2)+a1)
        return(N0)

    def Nmax_SM(N, Nmax, BD, LW):
        SM = (p0*((1-N/Nmax)/(p1-N/Nmax))-LW)*BD
        return SM

    def N0_SM(N, N0, BD, LW):
        SM = ((a0 * (1 / (N / N0 - a1)) - (a2))-LW)*BD
        return SM

    # set how many multiples of the 24 hour average STD should be used for filtering the data
    ################################################################################################################
    thres = 2

    # get all files in folder
    ################################################################################################################
    ################################################################################################################
    ################################################################################################################



    # make lists compareable


    ################################################################################################################
    ################################################################################################################

    # intiate lists to hold the processed information
    Calibrations = []
    CR_all = []
    C_all = []



    # Keep track of calibration RMSEs
    ListofRMSEs = []
    ListofFiles = []




    # load CR data
    ################################################################################################################
    ################################################################################################################

    CR_orig = pd.read_csv(data, low_memory=False, index_col = False,parse_dates=[0], na_values='noData')



    CR_orig['Time'] = pd.to_datetime(CR_orig['Time'], utc=True)
    CR_orig['Time'] = CR_orig['Time'].dt.tz_localize(None)
    CR_orig = CR_orig.set_index('Time')

    CR_orig = CR_orig.filter(regex="^(.(?!QualityFlag))*$")

    # resample the mean for all columns except precipitation, epithermal, slow --> sum
    col = CR_orig.filter(regex='Epithermal|Slow|Precipitation').columns
    CR = CR_orig[CR_orig.columns.difference(col)].resample('H').mean()
    CR[col] = CR_orig[col].resample('H').sum()

    # get unique column names to be able to proceed
    ################################################################################################################
    ################################################################################################################
    # Neutron counts, Temperature & rel. Humidity or abs. Humidity, Pressure
    cols = ['NeutronCount_Epithermal' in s and 'PreFlag' not in s for s in CR.columns]
    # Only use first Epithermal counter found - in Harrild there are two. But they were not both operated for the whole period
    # This makes calibration more complicated. Also the uncertainty estimation is more complicated then

    CR['NeutronCount_Epithermal'] = CR[CR.columns[cols][0]]

    CR_DWD = None
    # identify the pressure, humidity and temperature columns to use

    # pressure
    if 'AirPressure' in CR.columns:
        CR['pressure_use'] = CR['AirPressure']
        # get the mean of all available pressure columns
        mean_p = CR['pressure_use'].mean()
        # define a minimum and maximum threshold of the pressure --> why? # MS: yes, why?
        min_p = mean_p-mean_p*.05
        max_p = mean_p+mean_p*.05
        CR.loc[(CR['pressure_use'] < min_p) | (CR['pressure_use'] > max_p), 'pressure_use'] = np.nan

    elif 'RU_C_004' in CR_orig['feature'][0]  or 'RU_C_005' in CR_orig['feature'][0] or 'RU_C_006' in CR_orig['feature'][0]:
        if CR_DWD is None:
            data = download_dwd.download(dwd_map[CR_orig['feature'][0]], 'moisture', 'hourly', CR_orig.index[0])
            dataStream = StringIO(data)
            CR_DWD = pd.read_csv(dataStream, low_memory=False, index_col=False, na_values='-999.0', sep=';')
            CR_DWD['MESS_DATUM'] = pd.to_datetime(CR_DWD['MESS_DATUM'], format='%Y%m%d%H', utc=True)
            CR_DWD['MESS_DATUM'] = CR_DWD['MESS_DATUM'].dt.tz_localize(None)
            CR_DWD = CR_DWD.set_index('MESS_DATUM')
        CR['pressure_use'] = CR_DWD['P_STD']

    else:
        cols_p = ['Pressure' in s and 'PreFlag' not in s and 'NC' not in s for s in CR.columns]
        #print(CR[CR.columns[cols_p]].columns)
        CR_p = CR[CR.columns[cols_p]]
        # get the mean of all available pressure columns
        mean_p = CR_p.mean()
        # define a minimum and maximum threshold of the pressure
        min_p = mean_p-mean_p*.05
        max_p = mean_p+mean_p*.05
        # and apply this to the timeseres
        CR_p[(CR_p < min_p) | (CR_p > max_p)] = np.nan
        # use the average of all pressure columns as there should be only small differences between the individual ones
        CR['pressure_use'] = CR_p.mean(axis=1)

    # humidity
    if 'AirHumidity_Relative' in CR.columns:
        CR['humidity_use'] = CR['AirHumidity_Relative']
        CR.loc[(CR['humidity_use'] > 100) | (CR['humidity_use'] < 1), 'humidity_use'] = np.nan
    elif 'RU_C_004' in CR_orig['feature'][0]  or 'RU_C_005' in CR_orig['feature'][0] or 'RU_C_006' in CR_orig['feature'][0]:
        if CR_DWD is None:
            data = download_dwd.download(dwd_map[CR_orig['feature'][0]],'moisture','hourly', CR_orig.index[0])
            dataStream = StringIO(data)
            CR_DWD = pd.read_csv(dataStream, low_memory=False, index_col=False, na_values='-999.0',sep=';')
            CR_DWD['MESS_DATUM'] = pd.to_datetime(CR_DWD['MESS_DATUM'], format='%Y%m%d%H', utc=True)
            CR_DWD['MESS_DATUM'] = CR_DWD['MESS_DATUM'].dt.tz_localize(None)
            CR_DWD = CR_DWD.set_index('MESS_DATUM')


        result = pd.merge(CR_orig, CR_DWD, left_index=True, right_index=True, how="outer")


        CR['humidity_use'] = CR_DWD['RF_STD'] #result['RF_STD']

    else:
        cols_h = ['Humidity' in s and 'PreFlag' not in s and 'NC' not in s for s in CR.columns]
        #print(CR[CR.columns[cols_h]].columns)
        CR_h = CR[CR.columns[cols_h]]
        # first set all relative humidities > 100 an < 1 nan
        CR_h[CR_h > 100] = np.nan
        CR_h[CR_h < 1] = np.nan
        # get the mean of all available humidity columns
        mean_h = CR_h.mean()
        # as there is sometimes humidity measured in the detector/logger
        # these columns should not be used --> always use the column with largest avg humidity
        col_h = mean_h[mean_h == mean_h.max()].index
        CR['humidity_use'] = CR_h[col_h]

    # temperature
    if 'AirTemperature' in CR.columns:
        CR['temperature_use'] = CR['AirTemperature']
        CR.loc[(CR['temperature_use'] > 100) | (CR['temperature_use'] < - 50), 'temperature_use'] = np.nan

    elif 'RU_C_004' in CR_orig['feature'][0]  or 'RU_C_005' in CR_orig['feature'][0] or 'RU_C_006' in CR_orig['feature'][0]:
        if CR_DWD is None:
            data = download_dwd.download(dwd_map[CR_orig['feature'][0]], 'moisture', 'hourly', CR_orig.index[0])
            dataStream = StringIO(data)
            CR_DWD = pd.read_csv(dataStream, low_memory=False, index_col=False, na_values='-999.0', sep=';')
            CR_DWD['MESS_DATUM'] = pd.to_datetime(CR_DWD['MESS_DATUM'], format='%Y%m%d%H', utc=True)
            CR_DWD['MESS_DATUM'] = CR_DWD['MESS_DATUM'].dt.tz_localize(None)
            CR_DWD = CR_DWD.set_index('MESS_DATUM')

        CR['temperature_use'] = CR_DWD['TT_STD']


    else:
        cols_t = ['Temperature' in s and 'PreFlag' not in s and 'NC' not in s for s in CR.columns]
        #print(CR[CR.columns[cols_t]].columns)
        CR_t = CR[CR.columns[cols_t]]
        # set all temperatures > 100 and < -50 nan
        CR_t[CR_t > 100] = np.nan
        CR_t[CR_t < -50] = np.nan
        # get the mean of all available temperature columns
        mean_t = CR_t.mean()
        # as with humidity some times temperature is measuered in the detector
        # these cols should not be used. Decide by mean temp --> use lowest avg temp
        col_t = mean_t[mean_t == mean_t.min()].index
        CR['temperature_use'] = CR_t[col_t]

    # get absolute humidity from temperature and relative humidity
    if 'AirHumidity_Absolute_2m_Avg30min_HMP' not in CR.columns:
        # calculate absolute humidity
        CR['AirHumidity_Absolute'] = 6.112 * np.exp(17.67 * CR['temperature_use'] / (243.5 + CR['temperature_use'])) / (273.15 + CR['temperature_use']) * 2.1674 * CR['humidity_use']
    else:
        CR['AirHumidity_Absolute'] = CR['AirHumidity_Absolute_2m_Avg30min_HMP']
    CR.loc[CR['AirHumidity_Absolute'] <= 0, 'AirHumidity_Absolute'] = np.nan # remove air humidites = 0
    CR.loc[CR['AirHumidity_Absolute'] > 40, 'AirHumidity_Absolute'] = np.nan # remove air humidites > 40

    CR['humidity_use_cleaned'] = CR['AirHumidity_Absolute']  # initiate new series for cleaned humidity

    CR['AirHumidity_gapfilled'] = CR['humidity_use_cleaned']  # initiate gapfilled data

    CR['pressure_use_cleaned'] = CR['pressure_use']  # initiate new seried for cleaned pressure

    CR['AirPressure_gapfilled'] = CR['pressure_use_cleaned']  # initiate gapfilled data



    # neutron cleaning
    ################################################################################################################
    ################################################################################################################
    # do an initial cleaning of neutron counts
    # first eliminate 0-counts and counts > 3 the average to ensure proper rolling means can be obtained
    CR['Flag_Extreme_Counts'] = 0
    CR.loc[CR['NeutronCount_Epithermal'] > 10000, 'Flag_Extreme_Counts'] = 1
    CR.loc[CR['NeutronCount_Epithermal'] < 50,    'Flag_Extreme_Counts'] = 1

    CR.loc[CR['NeutronCount_Epithermal'] > 10000, 'NeutronCount_Epithermal'] = np.nan
    CR.loc[CR['NeutronCount_Epithermal'] < 50, 'NeutronCount_Epithermal'] = np.nan

    # then use the new series and based on thresholds and remove counts > 1.7x and smaller 1/2 the average
    #CR.loc[CR['NeutronCount_Epithermal'] < CR['NeutronCount_Epithermal'].mean()/2, 'NeutronCount_Epithermal'] = np.nan
    #CR.loc[CR['NeutronCount_Epithermal'] > CR['NeutronCount_Epithermal'].mean()*1.7, 'NeutronCount_Epithermal'] = np.nan

    # get uncertainty (std) of hourly and 24 hourly neutron counts -- this is based on RAW counts therefore calculated based on this and propagated to corrected counts later
    # hourly
    CR['NeutronCount_Epithermal_std'] = CR['NeutronCount_Epithermal']**.5 # hourly
    # 24-hourly rolling sum neutron counts
    CR['NeutronCount_Epithermal_Cum24h'] = CR['NeutronCount_Epithermal'].rolling(24, center=True, min_periods=12).sum() # 24 hourly - first get the 24 hour sum
    # 24-hourly rolling sum std
    CR['NeutronCount_Epithermal_Cum24h_std'] = CR['NeutronCount_Epithermal_Cum24h']**.5 # then get the uncertainty associated to this

    # get rolling mean and use the uncertainty as threshold
    ################################################################################################################
    ################################################################################################################
    Rol = CR.copy()
    Rol.drop(Rol.columns.difference(['NeutronCount_Epithermal', 'NeutronCount_Epithermal_Cum24h_std']), 1, inplace=True)

    # get the rolling mean (24h)
    Rol['NeutronCount_Epithermal_Avg24h'] = Rol['NeutronCount_Epithermal'].rolling(24, center=True, min_periods=12).mean()

    # get timeseries thresholds based on the std
    Rol['STD_xtimes'] = Rol['NeutronCount_Epithermal_Cum24h_std']*thres#/24*thres# + Rol['NeutronCount_Epithermal_Avg24h'] * thres

    Rol['Nmin'] = Rol['NeutronCount_Epithermal_Avg24h'] - Rol['STD_xtimes']
    Rol['Nmax'] = Rol['NeutronCount_Epithermal_Avg24h'] + Rol['STD_xtimes']
    # apply threshold
    Rol.loc[(Rol['Nmax'] > Rol['NeutronCount_Epithermal']) & (Rol['Nmin'] < Rol['NeutronCount_Epithermal']),'cleaned'] = Rol.loc[
        (Rol['Nmax'] > Rol['NeutronCount_Epithermal']) & (Rol['Nmin'] < Rol['NeutronCount_Epithermal']), 'NeutronCount_Epithermal']
    # and copy to CR dataframe
    CR['NeutronCount_Epithermal_Cum1h_cleaned'] = Rol['cleaned']

    # corrections
    ################################################################################################################
    ################################################################################################################
    # get neutron monitor counts

    ic = msg['data_ic']

    # finde header
    tmp = ""
    for line in ic.splitlines():
        if line.startswith('#'):
            tmp += line[1:] + '\n'
        else:
            tmp += line + '\n'
    data_ic = StringIO(tmp)


    NM = pd.read_csv(data_ic, comment='#', low_memory=False, na_values='noData', sep=';')
    NM.columns = NM.columns.str.strip()
    NM['Date_Time'] = pd.to_datetime(NM['Date_Time'], utc=True, format='%Y-%m-%d %H:%M:%S')
    NM['Date_Time'] = NM['Date_Time'].dt.tz_localize(None)
    NM = NM.set_index('Date_Time')


    I_ref = 150; Rc_NM = 4.49
    #NM = pd.read_pickle('data/ATHN.pkl'); I_ref = 52; Rc_NM = 8.53

    # get correction for pressure, humidity and incoming counts
    station_Rc = ''
    splitted_line  = msg['description'].split('----')

    if 'cutoff rigidity' in splitted_line[0]:
        station_Rc = float(splitted_line[0].split(': ')[1])

    l1 = splitted_line[1]
    index = l1.rfind(']')
    header = l1[0:index+1]
    data = l1[index:]




    Params = pd.read_csv(calibration_data, comment='#', low_memory=False, parse_dates=[0],
                     index_col=0, na_values='noData')
    print(Params)
    # give it proper timestamps
    Params['Calibration Time'] = Params.index
    Params['Calibration Time'] = pd.to_datetime(Params['Calibration Time'], format='%d.%m.%Y %H:%M').dt.round(
        freq='H')  # convert to datetime

    BD = np.nanmean(Params['BD [g/cm3]'])
    LW = np.nanmean(Params['LW [g/g]'])
    SM_ref = np.array(Params['SM [m3/m3]'])


    beta = 0.0076
    #beta = corny.estimate_beta_from_Rc(station_Rc)

    CR['cor_p'] = np.exp(beta * (CR['AirPressure_gapfilled'] - 1013.25))  # pressure correction (Desilets & Zreda, 2003) # 1012.25
    CR['cor_h'] = 1 + 0.0054 * (CR['AirHumidity_gapfilled'] - 0)  # humidity correction (Rosolem et al., 2013)
    CR.loc[CR['cor_h'].isna(), 'cor_h'] = 1 + 0.0054 * (CR['AirHumidity_gapfilled'] - 0) # I think this is arbitrary
    CR['cor_i'] = corny.C_inc(NM['N_Cts'], Iref=I_ref, method='Hawdon et al. (2014)', Rc=station_Rc, Rc_NM=Rc_NM)

    CR['biomass'] = np.nan
    # add vegetation correction for WU1
    if CR_orig['feature'][0] == 'WU_C_001':
        # construct a biomass df always from april to october biomass growth and before 2014 forest
        d = [CR.index.min(), '2014-01-01', '2014-01-01 01:00', '2014-04-01', '2014-10-01', '2015-04-01', '2015-10-01', '2016-04-01', '2016-10-01', '2017-04-01', '2017-10-01', '2018-04-01', '2018-10-01', CR.index.max()]
        b = [30, 30, 13.1, 13.1, 13.1, 13.1, 13.1, 13.1, 13.1, 13.1, 13.1, 13.1, 13.1, 13.1]
        bio = pd.DataFrame([d, b]).T
        bio.columns = ['DateTime_utc', 'biomass']
        bio['DateTime_utc'] = pd.to_datetime(bio['DateTime_utc'], utc=True)
        bio = bio.set_index('DateTime_utc')
        CR['biomass'] = bio['biomass'].astype(float)
        CR['biomass'] = CR['biomass'].interpolate()
        CR['cor_v'] = 1/(1-11.19/1210*CR['biomass'])
        CR = CR[CR.index > pd.to_datetime('2011-04-01', utc=True)] # before 2011-04 unexpected behaviour
        # new detector correction
        t1 = pd.to_datetime('2019-07-10', utc=True)
        bef = CR.loc[(CR.index > t1-pd.Timedelta('365Days')) & (CR.index < t1),'NeutronCount_Epithermal_Cum1h_cleaned']
        aft = CR.loc[(CR.index > t1) & (CR.index < t1+pd.Timedelta('365Days')),'NeutronCount_Epithermal_Cum1h_cleaned']
        CR.loc[CR.index > t1,'cor_nd'] = bef.mean()/aft.mean()
        CR.loc[CR.index <= t1, 'cor_nd'] = 1
    else:
        CR['cor_v'] = 1
        CR['cor_nd'] = 1

    # apply the corrections to the epithermal neutrons
    CR['NeutronCount_Epithermal_Cum1h_corrected'] = CR['NeutronCount_Epithermal_Cum1h_cleaned']         * CR['cor_p'] * CR['cor_i'] * CR['cor_h'] * CR['cor_v']*CR['cor_nd']
    # propagate the uncertainty from raw to corrected hourly neutron counts
    CR['NeutronCount_Epithermal_Cum1h_corrected_std'] = CR['NeutronCount_Epithermal_std']         * CR['cor_p'] * CR['cor_i'] * CR['cor_h'] * CR['cor_v']*CR['cor_nd']

    # 24h moving average
    CR['NeutronCount_Epithermal_MovAvg24h_corrected'] = CR['NeutronCount_Epithermal_Cum1h_corrected'].rolling(24, center=True, min_periods=12).mean()
    CR['NeutronCount_Epithermal_MovAvg24h_corrected_std'] = CR['NeutronCount_Epithermal_Cum1h_corrected_std'].rolling(24, center=True, min_periods=12).mean()/np.sqrt(24)

    #get calibration information

    Calibrations.append([])
    C_all.append([])

    ## get footprint metrics (R86 and D86) <- this takes really long because of the iteration. But I don't know how to solve it without...
    #################################################################################################################
    #################################################################################################################
    # F_metrics = []
    # for k in range(len(CR)):
    #    F_metrics.append(F_shape(CR.iloc[k]['SM_init'], CR.iloc[k]['AirPressure_gapfilled'], CR.iloc[k]['AirHumidity_gapfilled'], BD, LW))
    # CR[['R86', 'D86']] = F_metrics

    if 'SM' in CR.columns:
        CR['Footprint_Depth_m'] = corny.D86(CR['SM'] + LW, bd=BD, r=1) / 100
        CR['Footprint_Radius_m'] = CR.apply(lambda row: corny.get_footprint(
            row['SM'] + LW, row['AirHumidity_gapfilled'], row['AirPressure_gapfilled']), axis=1)
        ListofFiles2.append(files2[i])
        ListofDepth.append(CR['Footprint_Depth_m'].mean())
        ListofRadii.append(CR['Footprint_Radius_m'].mean())

        # Export
        CR_Export = CR[[
            'NeutronCount_Epithermal_Cum1h_corrected','NeutronCount_Epithermal_Cum1h_corrected_std',
            'NeutronCount_Epithermal_MovAvg24h_corrected','NeutronCount_Epithermal_MovAvg24h_corrected_std',
            'Flag_Extreme_Counts','Flag_Porosity_Excess',
            'SM_real', 'Uncertainty_sym_m3m3', 'Uncertainty_negative', 'Uncertainty_positive',
            'biomass']
          ].copy()
        CR_Export.columns = [
            'NeutronCount_Epithermal_Cum1h_corrected','NeutronCount_Epithermal_Cum1h_corrected_std',
            'NeutronCount_Epithermal_MovAvg24h_corrected','NeutronCount_Epithermal_MovAvg24h_corrected_std',
            'Flag_Extreme_Counts','Flag_Porosity_Excess',
            'SoilMoisture_volumetric_MovAvg24h','SoilMoisture_volumetric_MovAvg24h_std',
            'SoilMoisture_volumetric_MovAvg24h_lower','SoilMoisture_volumetric_MovAvg24h_upper', 'Biomass']


        print(CR_Export)

    #################################################################################################################
    #################################################################################################################

    # append CR data to list of CR files
    CR_all.append(CR)



    Lists = pd.DataFrame()

    Lists['RMSE'] = ListofRMSEs



    # In[14]:


    print('Calibration RMSE: %.4f' % Lists[Lists.RMSE>0.0001]['RMSE'].mean())

    print(CR_all)
