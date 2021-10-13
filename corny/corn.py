"""
CoRNy CORN
    Functions specific for data processing of COsmic-Ray Neutrons
    from: https://git.ufz.de/CRNS/cornish_pasdy/-/blob/master/corny/corn.py
    version: 0.62
"""
import pandas as pd
import numpy as np
import os

#####################
#   Cleaning        #
#####################

"""
    Infer time resolution
"""
def infer_tres(data, default=None):
    if default:
        return(int(default))
    else:
        # infer from timestamp difference
        try:
            return(data.index.to_series().diff()) #.median().seconds
        except:
            # set 60 sec as the fallback time resolution
            return(60)

"""
    Unit_convert(data[N], data[tres], 'cph')
"""
def Unit_convert(counts, unit1=None, unit2=None):
    if unit2 == 'cph':
        factor = 3600
    if isinstance(unit1, pandas.Series):
        return( counts / unit1 * factor )

def get_nans(data):
    return(data.isnull().sum().sum())

def find_outlier(data_orig, column, target=None, lower=None, upper=None, n_sigma=None, sigma=None, fill=None, action=None):

    #[print("%d " % x, end='') for x in data.loc[(data[column] > upper), column ].values]

    if fill is None:
        fill = np.nan
    if target is None:
        target = column

    data = data_orig.copy()
    data[target] = data[target].astype(float)
    before = get_nans(data)

    if not lower is None:
        #data.loc[(data[column] < lower), [column, target] ].to_csv('outlier-'+column+target)
        data.loc[(data[column] < lower), target ] = fill
    if not upper is None:
        #data.loc[(data[column] > upper), [column, target] ].to_csv('outlier-'+column+target)
        data.loc[(data[column] > upper), target ] = fill
    if n_sigma:
        temp = '__temp'
        diff = '__diff'
        data[temp] = n_sigma * data[sigma]
        data[diff] = np.abs(data[column].diff()) /2

        #data.loc[(data[diff] > data[temp] ), [diff, temp, target] ].to_csv('outlier-'+column+target+'diff')
        data.loc[(data[diff] > data[temp] ), target ] = fill

        del data[temp]
        del data[diff]

    n_outliers = get_nans(data) - before
    if n_outliers > 0:
        if action == 'drop':
            data = data.dropna(subset=[target])
            print('i Dropped %d invalid values in "%s"' % (n_outliers, column))
        else:
            print('i   Found %d invalid values in "%s"' % (n_outliers, column))

    return(data[target])


def fill_gaps(data, column, var='pressure', fill=None, fill_type=float,
              n_stations=4, lon=None, lat=None, alt=None, T=None,
              local_storage_name='', verbose=True):
    """
    Fill nan in pandas.Series with value or DWD data
    """
    if data[column].isnull().any():
        if fill=='DWD':
            data[column] = fill_gaps_DWD(data, column, var=var, n_stations=n_stations,
                            lon=lon, lat=lat, alt=alt, T=T,
                            local_storage_name=local_storage_name, verbose=verbose)
        else:
            # Fill with value from config
            data[column].fillna(safe_cast(fill, fill_type), inplace=True)
    else:
        if verbose: print('i No nan values in the %s data, no need to gapfill.' % var)

    return(data[column])

def fill_gaps_DWD(data, column, var='pressure', n_stations=4,
                  lon=None, lat=None, alt=None, T=None,
                  local_storage_name='', verbose=True):
    """
    Fill nan in a pandas.Series with DWD data
    """
    # Check coordinates
    if not lat or not lon:
        print(cprintf('! Cannot use DWD lookup, no coordinates given (you may check config:info:coords)','red'))
        return(np.nan)

    #Estimate the temporal resolution for the dwd data in seconds
    temporal_resolution=infer_tres(data).mean().total_seconds()
    #determine the temporal resolution string for dwd
    if temporal_resolution >= 86400:
        dwd_resolution='daily'
    elif temporal_resolution >= 3600:
        dwd_resolution='hourly'
    else:
        dwd_resolution='10_minutes'

    #print('Temporal Resolution to retrieve DWD data is ',dwd_resolution )

    # Prepare
    #if verbose: print(cprintf('>     Downloading %s data from DWD source...' % var, 'yellow'))
    if var == 'pressure':
        dwd_var = 'air_pressure_nn'
        if dwd_resolution=='10_minutes':
            dwd_cat='air_temperature'
        else:
            dwd_cat = 'pressure'
        unit = 'hPa'

    elif var == 'temperature':
        dwd_cat = 'air_temperature'
        if dwd_resolution=='10_minutes':
            dwd_var = 'air_temperature_at_2m_height'
        else:
            dwd_var = '2m_air_temperature'
        unit = 'C'

    elif var == 'humidity':
        dwd_cat = 'air_temperature'
        #variable name depends on resolution
        if dwd_resolution=='10_minutes':
            dwd_var = 'relative_humidity_at_2m_height'
        else:
            dwd_var = '2m_relative_humidity'
        unit = '%'

    else:
        print(cprintf('! Not sure what variable to look up at DWD, gap filling stopped.'))
        return(data)

    # select all nan values
    data_subset = data[data[column].isnull()]

    #check whether the dwd data is downloaded already

    local_storage_file = local_storage_name + '-' + var + '_from_DWD.csv'
    #dwd_directory=os.path.join('ancillary_data',
    #                            os.path.split(data.attrs['configfile'])[1].replace('.','_'),
    #                            'dwd')
    #add to attributes
    #data_subset.attrs['dwd_path']=dwd_directory
    #data_subset.attrs['target_var']=var
    #os.makedirs(dwd_directory,exist_ok=True)

    #if 'dwd_'+var+'.csv' not in os.listdir(dwd_directory):
    if os.path.isfile(local_storage_file):
        print(cprintf('>     Reading DWD data from ' + local_storage_file, 'yellow'))

        data_dwd_local = pd.read_csv(local_storage_file)
        data_dwd_local = data_dwd_local.reset_index(drop=True).set_index(pd.to_datetime(data_dwd_local[data_subset.index.name]),drop=True)
        data_subset    = data_dwd_local.drop(columns=[data_subset.index.name])

    else:
        # run API
        print('| Online lookup for DWD data...')
        data_subset = exdata.meteoservice.retrieve_dwd_data(data_subset,
                          lon = lon, lat = lat,
                          dwd_category=dwd_cat, dwd_parameters=[dwd_var],
                          no_of_nearest_stations = n_stations,temporal_resolution=dwd_resolution,
                          local_storage_file=local_storage_file)

    if var == 'pressure':
        # Rescale pressure from sealevel to altitude
        data_subset[dwd_var] = pressure_asl2alt(data_subset[dwd_var],
                                alt=data_subset[alt], T=data_subset[T])
        # clean again
        data_subset = data_subset[data_subset[dwd_var] > 1]

    # replace
    data.loc[data_subset.index, column] = data_subset[dwd_var]

    # report
    print('i     Replaced %d values by %s = %.1f +/- %.1f %s from DWD.'% (
        len(data_subset), column, data_subset[dwd_var].mean(),
        data_subset[dwd_var].std(), unit))

    return(data[column])


#####################
#   Uncertainty     #
#####################

def N_err(N):
    return(np.sqrt(N))


#####################
#   Corrections     #
#####################

def pressure_asl2alt(p0, alt=None, T=None):
    """
    Convert air pressure at sea level to air pressure at a given altitude
    """
    if alt is None:
        print(cprintf('! Attempt to rescale sealevel to local pressure, but altitude is missing.', 'red'))
        return(np.nan)

    if T is None:
        print(cprintf('! Attempt to rescale sealevel to local pressure, but temperature is missing. '
                        + 'Assuming 15 degree Celsius.', 'red'))
        T = 288.15

    p = p0 * ( 1 - (0.0065*alt) / ( T + 0.0065*alt + 273.15 ) )**5.257
    return(p)


"""
    lattice water
"""
def lw_from_clay(clay, method='Greacen et al. 1981'):
    if method == 'Greacen et al. 1981':
        return(clay * 0.1783)

"""
    organic water equivalent
"""
def owe_from_corg(Corg, method='Franz et al. 2015'):
    if method == 'Franz et al. 2015':
        return(Corg * 0.556)

    
def estimate_beta_from_Rc(R):
    """
    Estimate beta based on relationship to rigidity.
    Approximated roughly from crnslab.org using constant atm depth.
    """
    return(1/(135.2+0.21*np.exp(R/2.5)))

"""
    correct_p(pressure, reference, beta)
    = float or df
    Correction of incoming neutron flux by air pressure
"""
def C_press(p, pref=1013.15, beta=136, method='Zreda et al. (2012)', inclination=None):
    r = 1
    if method == 'Zreda et al. (2012)':
        r = np.exp((p - pref) / beta)
    elif method == 'Dunai et al. (2000)':
        beta = 129.55 + 19.85 / (1+np.exp((inclination-62.05)/5.43))**3.59
        r = np.exp((p - pref) / beta)
    else:
        print('No pressure correction method applied.')
        pass
    return(r)

"""
    returns 1 by default
"""
def C_humid(h, href=0, alpha=0.0054, method='Rosolem et al. (2013)'):
    r = 1
    if method == 'Rosolem et al. (2013)':
        r = 1 + alpha * (h - href)
    elif method == 'Koehli et al. (2021)':
        print('i Note: Humidity correction after Koehli et al 2021 will be applied during soil moisture conversion.')
        pass
    else:
        print('No humidity correction method applied.')
        pass
    return(r)

"""
    incoming
"""
def C_inc(I, Iref=0, gamma=1, method='Zreda et al. (2012)', Rc=None, Rc_NM=None):
    r = 1
    if method == 'Zreda et al. (2012)':
        r = Iref / I

    elif method == 'Rotunno and Zreda (2014)':
        if Rc is None:
            print('Rigidity data incomplete, taking given gamma = ' +str(gamma))
        else:
            gamma = 0.871+0.0064*Rc
        r = 1/(1 - gamma * (1 - I / Iref))

    elif method == 'Hawdon et al. (2014)':
        if Rc_NM is None or Rc is None:
            print('Rigidity data incomplete, taking given gamma = ' +str(gamma))
        else:
            gamma = 1 - 0.075*(Rc - Rc_NM)
        r = 1/(1 - gamma * (1 - I / Iref))

    elif method == 'Schroen et al. (2015)':
        r = 1/(1 - gamma * (1 - I / Iref))

    else:
        print('No incoming correction method applied.')
        pass
    return(r)

# Conversion

"""
    rh2ah(relative_humidity, temperature)
    = float
    Calculates absolute humidity
"""
def abs_humidity(rh, Tem):
    ah = 6.112*np.exp(17.67*Tem/(243.5+Tem))/(273.15+Tem) * 2.1674 * rh
    return(ah)

rh2ah = abs_humidity


def sm2N(sm, N0, off=0.02, bd=1, a0=0.0808, a1=0.115, a2=0.372):
    return(N0*(0.0808/(sm/bd+0.115+off)+0.372))

def sm2N_Koehli(sm, h=9, off=0.02, bd=1, func='vers1', method=None, bio=0):
    #vers1: Sep25_responsef, Sep25_Ewindow, vers2: Jan23_uranos, Jan23_mcnpfull, Mar12_atmprof

    # total sm
    smt = sm + off
    smt *= 1.43/bd
    if smt == 0.0:
        smt = 0.001
    # nothing to do with bd
    p = []

    ################# PLEASE DOUBLE-CHECK THE FUNCTIONS AND VALUES ##################

    if func == 'vers1':
        if method == 'Sep25_responsef':          p = [4.179, 0.0230, 0.200, 1.436, 0.902, -0.00308, -0.0716, -0.0000163, 0.00164]
        elif method == 'Sep25_Ewindow':          p = [8.284, 0.0191, 0.143, 2.384, 0.760, -0.00344, -0.1310, -0.0000240, 0.00280]

        N = (p[1]+p[2]*smt)/(smt+p[1])*(p[0]+p[6]*h +p[8]* h**2+p[7]*h**3) + np.exp(-p[3]*smt)*(p[4]+p[5]*h)

    elif func == 'vers2':
        if method == 'Jan23_uranos':             p = [4.2580, 0.0212, 0.206, 1.776, 0.241, -0.00058, -0.02800, 0.0003200, -0.0000000180]
        elif method == 'Jan23_mcnpfull':         p = [7.0000, 0.0250, 0.233, 4.325, 0.156, -0.00066, -0.01200, 0.0004100, -0.0000000410]
        elif method == 'Mar12_atmprof':          p = [4.4775, 0.0230, 0.217, 1.540, 0.213, -0.00022, -0.03800, 0.0003100, -0.0000000003]

        elif method == 'Mar21_mcnp_drf':         p = [1.0940, 0.0280, 0.254, 3.537, 0.139, -0.00140, -0.00880, 0.0001150,  0.0000000000]
        elif method == 'Mar21_mcnp_ewin':        p = [1.2650, 0.0259, 0.135, 1.237, 0.063, -0.00021, -0.01170, 0.0001200,  0.0000000000]
        elif method == 'Mar21_uranos_drf':       p = [1.0240, 0.0226, 0.207, 1.625, 0.235, -0.00290, -0.00930, 0.0000740,  0.0000000000]
        elif method == 'Mar21_uranos_ewin':      p = [1.2230, 0.0185, 0.142, 2.568, 0.155, -0.00047, -0.01190, 0.0000920,  0.0000000000]

        elif method == 'Mar22_mcnp_drf_Jan':     p = [1.0820, 0.0250, 0.235, 4.360, 0.156, -0.00071, -0.00610, 0.0000500,  0.0000000000]
        elif method == 'Mar22_mcnp_ewin_gd':     p = [1.1630, 0.0244, 0.182, 4.358, 0.118, -0.00046, -0.00747, 0.0000580,  0.0000000000]
        elif method == 'Mar22_uranos_drf_gd':    p = [1.1180, 0.0221, 0.173, 2.300, 0.184, -0.00064, -0.01000, 0.0000810,  0.0000000000]
        elif method == 'Mar22_uranos_ewin_chi2': p = [1.0220, 0.0218, 0.199, 1.647, 0.243, -0.00029, -0.00960, 0.0000780,  0.0000000000]
        elif method == 'Mar22_uranos_drf_h200m': p = [1.0210, 0.0222, 0.203, 1.600, 0.244, -0.00061, -0.00930, 0.0000740,  0.0000000000]

        elif method == 'Aug08_mcnp_drf':         p = [1.110773444917129, 0.034319446894963, 0.180046592985848, 1.211393214064259, 0.093433803170610, -1.877788035e-005, -0.00698637546803, 5.0316941885e-005, 0.0000000000]
        elif method == 'Aug08_mcnp_ewin':        p = [1.271225645585415, 0.024790265564895, 0.107603498535911, 1.243101823658557, 0.057146624195463, -1.93729201894976, -0.00866217333051, 6.198559205414182, 0.0000000000]
        elif method == 'Aug12_uranos_drf':       p = [1.042588152355816, 0.024362250648228, 0.222359434641456, 1.791314246517330, 0.197766380530824, -0.00053814104957, -0.00820189794785, 6.6412111902e-005, 0.0000000000]
        elif method == 'Aug12_uranos_ewin':      p = [1.209060105287452, 0.021546879683024, 0.129925023764294, 1.872444149093526, 0.128883139550384, -0.00047134595878, -0.01080226893400, 8.8939419535e-005, 0.0000000000]
        elif method == 'Aug13_uranos_atmprof':   p = [1.044276170094123, 0.024099232055379, 0.227317847739138, 1.782905159416135, 0.198949609723093, -0.00059182327737, -0.00897372356601, 7.3282344356e-005, 0.0000000000]
        elif method == 'Aug13_uranos_atmprof2':  p = [4.31237,           0.020765,          0.21020,           1.87120,           0.16341,           -0.00052,          -0.00225,          0.000308,         -1.9639e-8]

        N = (p[1]+p[2]*smt)/(smt+p[1])*(p[0]+p[6]*h+p[7]*h**2+p[8]*h**3/smt)+np.exp(-p[3]*smt)*(p[4]+p[5]*(h + bio/5*1000))

    return(N)#/N.mean())


def Calibrate_N0_Desilets(N, sm, bd=1, lw=0, owe=0, a0=0.0808, a1=0.372, a2=0.115):
    return(N/(a0 / (sm/bd + a2 + lw + owe) + a1))

def N2SM_Desilets(N, N0, bd=1, lw=0, owe=0, a0=0.0808, a1=0.372, a2=0.115):
    return((a0/(N/int(N0)-a1)-a2 -lw - owe) * bd)

def N2SM_Schmidt_single(N, hum, bd=1, lw=0, owe=0, method='Mar21_uranos_drf'):
    t0 = 0.0
    t1 = 1.0
    n0 = sm2N_Koehli(0.0, hum, method=method, func='vers2', off=lw+owe, bd=bd)
    n1 = sm2N_Koehli(1.0, hum, method=method, func='vers2', off=lw+owe, bd=bd)
    while t1 - t0 > 0.0001:
        t2 = 0.5*(t0+t1);
        n2 = sm2N_Koehli(t2, hum, method=method, func='vers2', off=lw+owe, bd=bd)
        if N < n2:
            t0 = t2
            n0 = n2
        else:
            t1 = t2
            n1 = n2
    t2 = 0.5*(t0+t1)
    return(t2)

def N2SM_Schmidt(data, Nstr, humstr, N0, bdstr='bd', lwstr='lw', owestr='owe', method='Mar21_uranos_drf'):
    sm = data.apply((lambda x: N2SM_Schmidt_single(x[Nstr]/N0*0.77, x[humstr], lw=x[lwstr], owe=x[owestr], bd=x[bdstr], method=method)), axis=1)
    return(sm)


def abl1(N, N0=1000, a0=0.0808, a1=0.372, a2=0.115): return(   -a0*N0/(a1*N0-N)**2 )
def abl2(N, N0=1000, a0=0.0808, a1=0.372, a2=0.115): return( 2*-a0*N0/(a1*N0-N)**3 )
def abl3(N, N0=1000, a0=0.0808, a1=0.372, a2=0.115): return( 6*-a0*N0/(a1*N0-N)**4 )

def theta(N, N0=1000, a0=0.0808, a1=0.372, a2=0.115):
    return(a0/(N/N0-a1)-a0)

def dtheta_low(N, N_err=None, N0=1000, ordnung=3, a0=0.0808, a1=0.372, a2=0.115):
    if N_err is None: N_err = np.sqrt(N)
    r = 0
    if ordnung >= 1: r += N_err    *abl1(N, N0, a0, a1, a2)
    if ordnung >= 2: r += N_err**2 *abl2(N, N0, a0, a1, a2) /2
    if ordnung >= 3: r += N_err**3 *abl3(N, N0, a0, a1, a2) /6
    return( r )

def dtheta_upp(N, N_err=None, N0=1000, ordnung=3, a0=0.0808, a1=0.372, a2=0.115):
    if N_err is None: N_err = np.sqrt(N)
    r = 0
    if ordnung >= 1: r += -N_err    *abl1(N, N0, a0, a1, a2)
    if ordnung >= 2: r +=  N_err**2 *abl2(N, N0, a0, a1, a2) /2
    if ordnung >= 3: r += -N_err**3 *abl3(N, N0, a0, a1, a2) /6
    return( r )

def dtheta_std(N, N_err=None, N0=1000, ordnung=3, a0=0.0808, a1=0.372, a2=0.115):
    if N_err is None: N_err = np.sqrt(N)
    r = 0
    if ordnung >= 1: r += N_err**2 *abl1(N, N0, a0, a1, a2)**2
    if ordnung >= 2: r += N_err**4 *abl2(N, N0, a0, a1, a2)**2 /2
    if ordnung >= 3: r += N_err**6 *abl3(N, N0, a0, a1, a2)**2 /36*15 + N_err**4 *abl1(N, N0, a0, a1, a2) *abl3(N, N0, a0, a1, a2)
    return( np.sqrt(r) )

def dtheta_stdx(N, N_err=None, N0=1000, a0=0.0808, a1=0.372, a2=0.115):
    if N_err is None: N_err = np.sqrt(N)
    return( (a0 *N0 *N_err *np.sqrt(8 *N_err**2 *(N - a1 *N0)**2 + (N - a1 *N0)**4 + 15 *N_err**4))/(N - a1 *N0)**4 )

# Error propagation for factors
def errpropag_factor(data, A, B, err='_err', err2=None):
    if err2 is None: err2 = err
    return(data[A] * data[B+err2] + data[A+err] * data[B])
    # dz/z=dx/x+dy/y with z=xy => dz = dx*y+dy*x


# Footprint

def D86(sm, bd=1, r=1):
    #return(1/bd*( 8.321+0.14249*( 0.96655+np.exp(-r/100))*(26.42+sm) / (0.0567+sm)))
    return(1/bd*( 8.321+0.14249*( 0.96655+np.exp(-r/100))*(20.0+sm) / (0.0429+sm)))

def Weight_d(d, D):
    return(np.exp(-2*d/D))



def report_N(data, column, correction='', units='cph'):
    mycolumns = [column, column+'_err']
    report(data, column, mycolumns, correction=correction, units=units, format='i  %-30s  %5.0f +/- %5.0f %s')

def report_SM(data, column, correction='', units='%'):
    mycolumns = [column, column+'_err_low', column+'_err_upp']
    data2 = data.copy()
    for c in mycolumns:
        data2[c] *= 100
    report(data2, column, mycolumns, correction=correction, units=units, format='i  %-30s  %3.0f %2.0f+%2.0f %s')

# Preload footprint radius matrix
preload_footprint_data = np.loadtxt('corny/footprint_radius.csv')


def get_footprint(sm, h, p, lookup_file=None):
    """
    usage: data['footprint_radius'] = data.apply(lambda row: get_footprint( row[smv], row[ah], row[p] ), axis=1)
    """
    if np.isnan(sm) or np.isnan(h) or np.isnan(p): return(np.nan)
    if sm <  0.01: sm =  0.01
    if sm >  0.49: sm =  0.49
    if h  > 30   : h  = 30
    #print(sm, h, p, int(round(100*sm)), int(round(h)))
    if lookup_file is None:
        footprint_data = preload_footprint_data
        #footprint_data = np.loadtxt(os.path.join(pasdy_path ,'corny/footprint_radius.csv'))
    elif isinstance(lookup_file, str):
        if os.path.exists(lookup_file):
            footprint_data = np.loadtxt(lookup_file)
        else:
            return(np.nan)
    elif isinstance(lookup_file, np.ndarray):
        footprint_data = lookup_file
    else:
        return(np.nan)
    return(footprint_data[int(round(100*sm))][int(round(h))] * 0.4922/(0.86-np.exp(-p/1013.25)))


def get_footprint_volume(depth, radius, theta, bd):
    return((depth + D86(theta, bd, radius))*0.01*0.47*radius**2*3.141 /1000)

    # 0.44 (dry) ..0.5 (wet) is roughly the average D over radii

def Wr_approx(r=1):
    return((30*np.exp(-r/1.6)+np.exp(-r/100))*(1-np.exp(-3.7*r)))
