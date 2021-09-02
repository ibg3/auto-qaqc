import pandas as pd
import numpy as np
import os
from scipy.optimize import minimize
from io import StringIO

from clisos_mod.clisos import CliSos


def execute(msg, data):

    # set max and min threshold for specific location --> I think this should be removed!!
    Nmax = 5000
    Nmin = 100
    # set how many multiples of the 24 hour average STD should be used for filtering the data
    thres = 20


    # define function to otimise N0 from several dates for RMSE
    ################################################################################################################
    a0 = 0.0808
    a1 = 0.372
    a2 = 0.115  # Desilets 2010

    # define function to minimize
    def RMSE_N0(n0):
        SM = BD * (a0 * (1 / (N / n0 - a1)) - (a2 - LW))  # calculate SM from Neutrons and N0
        return np.nanmean(((SM - SM_ref) ** 2))**.5  # return RMSE


    # load CRNS data (find header)
    tmp = ""
    for line in msg['orig_data'].splitlines():
        if line.startswith('#'):
            tmp += line[1:]+'\n'
        else:
            tmp += line+'\n'
    data = StringIO(tmp)


    # convert to pd df
    ################################################################################################################
    CR = pd.read_csv(data, comment='#', low_memory=False, parse_dates=[0],
                     index_col=0, na_values='noData', date_parser=lambda col: pd.to_datetime(col, format='%Y-%m-%dT%H:%M:%S.%f%z', utc=True))

    # only look at times where index is exxistant
    CR = CR[CR.index.notna()]
    print(CR)
    # sort out very extreme - measurements --> I think these should be removed??
    CR['NeutronCount_Epithermal_Cum1hr in [-]'][(CR['NeutronCount_Epithermal_Cum1hr in [-]'] > Nmax) | (
            CR['NeutronCount_Epithermal_Cum1hr in [-]'] < Nmin)] = np.nan  # apply thresholds

    # get uncertainty (std) of hourly and 24 hourly neutron counts -- this is based on RAW counts therefore calculated based on this and propagated to corrected counts later
    ################################################################################################################
    # hourly
    CR['NeutronCount_Epithermal_Cum1hr in [-]_std'] = CR['NeutronCount_Epithermal_Cum1hr in [-]']**.5 # hourly
    print(CR['NeutronCount_Epithermal_Cum1hr in [-]'])
    print(CR.columns)
    # 24-hourly
    CR['NeutronCount_Epithermal_Cum24hr in [-]'] = CR['NeutronCount_Epithermal_Cum1hr in [-]'].rolling(24, center=True,
                                                                                                       min_periods=1).sum() # 24 hourly - first get the 24 hour sum
    CR['NeutronCount_Epithermal_Cum24hr in [-]_std'] = CR['NeutronCount_Epithermal_Cum24hr in [-]']**.5 # then get the uncertainty associated to this
    
    # get rolling mean and use the uncertainty as threshold
    ################################################################################################################
    Rol = CR.copy()
    Rol.drop(Rol.columns.difference(['NeutronCount_Epithermal_Cum1hr in [-]', 'NeutronCount_Epithermal_Cum24hr in [-]_std']), 1, inplace=True)
    
    # get the rolling mean (24h)
    Rol['NeutronCount_Epithermal_Avg24h'] = Rol['NeutronCount_Epithermal_Cum1hr in [-]'].rolling(24, center=True,
                                                                                         min_periods=1).mean()
    
    # get timeseries thresholds based on the std
    Rol['STD_xtimes'] = Rol['NeutronCount_Epithermal_Cum24hr in [-]_std']/24*thres# + Rol['NeutronCount_Epithermal_Avg24h'] * thres
    
    Rol['Nmin'] = Rol['NeutronCount_Epithermal_Avg24h'] - Rol['STD_xtimes']
    Rol['Nmax'] = Rol['NeutronCount_Epithermal_Avg24h'] + Rol['STD_xtimes']
    # apply threshold
    Rol['cleaned'] = Rol['NeutronCount_Epithermal_Cum1hr in [-]'][
        (Rol['Nmax'] > Rol['NeutronCount_Epithermal_Cum1hr in [-]']) & (Rol['Nmin'] < Rol['NeutronCount_Epithermal_Cum1hr in [-]'])]
    
    CR['NeutronCount_Epithermal_Cum1h_cleaned'] = Rol['cleaned']
    
    # incoming counts from message object
    ################################################################################################################
    ic = msg['ic']
    
    # finde header
    tmp = ""
    for line in ic.splitlines():
        if line.startswith('#'):
            tmp += line[1:]+'\n'
        else:
            tmp += line+'\n'
    data_ic = StringIO(tmp)
    
    # convert to pandas df
    NM = pd.read_csv(data_ic, comment='#', low_memory=False, parse_dates=[0],
                     index_col=0, na_values='noData', date_parser=lambda col: pd.to_datetime(col, format='%Y-%m-%dT%H:%M:%S.%f%z', utc=True))
    
    # get correction(150 set as reference)
    #NM['cor'] = 1 + 1 * (150 / NM['NeutronCount_Epithermal_Cum1hr in [-]'] - 1)

    # get absolute humidity from temperature and relative humidity
    CR['AirHumidity_absolute_Avg1h'] = 6.112 * np.exp(
        17.67 * CR['AirTemperature in [degC]'] / (243.5 + CR['AirTemperature in [degC]'])) / (
                                               273.15 + CR['AirTemperature in [degC]']) * 2.1674 * CR[
                                           'AirHumidity_Relative in [%_Sat]']


    # correct for the influences of incoming radiation, pressure and humidity
    ################################################################################################################
    CR['cor_p'] = np.exp(0.0076 * (CR['AirPressure_2m in [mbar]'] - 1023.25))  # pressure correction (Desilets & Zreda, 2003)
    CR['cor_h'] = 1 + 0.0054 * (CR['AirHumidity_absolute_Avg1h'] - 0)  # humidity correction (Rosolem et al., 2013)
    CR['cor_i'] = 1 + 1 * (150 / NM['NeutronCount_Epithermal_Cum1hr in [-]'] - 1) # incoming correction (Desilets & Zreda, 2001)

    # apply the corrections to the epithermal neutrons
    CR['NeutronCount_Epithermal_Cum1h_corrected'] = CR['NeutronCount_Epithermal_Cum1h_cleaned'] * CR['cor_p'] * CR[
        'cor_i'] * CR['cor_h']
    # propagate the uncertainty from raw to corrected hourly neutron counts
    CR['NeutronCount_Epithermal_Cum1h_corrected_std'] = CR['NeutronCount_Epithermal_Cum1hr in [-]_std']* CR['cor_p'] * CR[
        'cor_i'] * CR['cor_h']

    # load calibration data
    ################################################################################################################
    calibration_data = StringIO(msg['calibration'])
    # convert to pd dataframe
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

    # get neutron counts for calibration time
    N = []
    Time = []
    print(CR.index)
    for i in range(len(Params['Calibration Time'])):
        Time.append(Params['Calibration Time'][i].tz_localize('utc'))
        print(CR.loc[CR.index == Time[i]])
        CR = CR.sort_index()
        n_tmp = CR.rolling('24H').apply(lambda x : np.nanmean(a=x))['NeutronCount_Epithermal_Cum1h_corrected'][
                     CR.index == Time[i]]
        N.append(n_tmp.values)
  
    N = np.array(N)  # convert to numpy array
    
    # find times wehre no reference inormation is existant
    to_delete = [] 
    if N:
        for i in range(len(N)):
            if not N[i]:
                to_delete.append(i)

        error_string = str(len(to_delete)) + ' elements did not match with calibration data.'
        msg['error'] = error_string
        print(error_string)

        N = np.delete(N, to_delete)
        SM_ref = np.delete(SM_ref, to_delete)
    print('N')
    print(N)
    print('SM_ref')
    print(SM_ref)
    print('to_delete')
    print(to_delete)
    # optimise N0
    ################################################################################################################
    res = minimize(RMSE_N0, 1000, method='nelder-mead', options={'xtol': 1e-8, 'disp': False})
    N0 = float(res.final_simplex[0][0])  # store result in N0
    
    
    
    # get 24 H rolling mean of corrected counts
    ################################################################################################################
    # uncertainty corrected 24 h Neuron counts
    CR['NeutronCount_Epithermal_Avg24h_corrected'] = CR['NeutronCount_Epithermal_Cum1h_corrected'].rolling(24,
                                                                                                           center=True,
                                                                                                           min_periods=1).mean()
    # get 24 H rolling mean uncertainty
    CR['NeutronCount_Epithermal_Avg24h_corrected_std'] = CR['NeutronCount_Epithermal_Cum24hr in [-]_std']/24 * CR['cor_p'].rolling(24, center=True, min_periods=1).mean() * CR['cor_i'].rolling(24, center=True, min_periods=1).mean() * CR['cor_h'].rolling(24, center=True, min_periods=1).mean()
    
    
    
    # convert 24 h values to soil moisture (Desilets et al., 2010)
    ################################################################################################################
    CR['SoilMoisture_volumetric'] = BD * (
            a0 * (1 / (CR['NeutronCount_Epithermal_Avg24h_corrected'] / N0 - a1)) - (a2 - LW))
    
    # soil moisture uncertainties
    ################################################################################################################
    # obtain "negative_STD"
    CR['SoilMoisture_volumetric_Negative_std'] = BD * (
            a0 * (1 / ((CR['NeutronCount_Epithermal_Avg24h_corrected']-CR['NeutronCount_Epithermal_Avg24h_corrected_std']) / N0 - a1)) - (a2 - LW)) - CR['SoilMoisture_volumetric']
    # and "positive STD"
    CR['SoilMoisture_volumetric_Positive_std'] = BD * (
            a0 * (1 / ((CR['NeutronCount_Epithermal_Avg24h_corrected']+CR['NeutronCount_Epithermal_Avg24h_corrected_std']) / N0 - a1)) - (a2 - LW)) - CR['SoilMoisture_volumetric']
    # good guess symmetrical STD (Jakobi et al., 2020)
    CR['SoilMoisture_volumetric_symmetric_std'] = BD * CR['NeutronCount_Epithermal_Avg24h_corrected_std'] * ((a0 * N0) / (CR['NeutronCount_Epithermal_Avg24h_corrected'] - a1 * N0)**4) *  ((CR['NeutronCount_Epithermal_Avg24h_corrected'] - a1 * N0)**4 + 8 * CR['NeutronCount_Epithermal_Avg24h_corrected_std']**2 * ((CR['NeutronCount_Epithermal_Avg24h_corrected'] - a1 * N0)**2) + 15 * CR['NeutronCount_Epithermal_Avg24h_corrected_std']**4)**.5

    return CR.to_csv()