import datetime
import io
try:
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
except:
    pass
try:
    import numpy as np
except:
    pass

def pk1(pk):
    return {True: lambda: pk[1],False: lambda: ""}.get(len(pk)>1)()

def __plotData(data,fmt):
    plottingDataAll={}
    defaultTimestampPattern='%Y-%m-%dT%H:%M:%S.%f'
    # pk=(TimeStamp,StationId)
    pks=list(data.keys())
    pks.sort()
    #print pks
    if fmt!=None:
            fmt=fmt.split(',')
    else:
        fmt=['b-','g-','r-','c-','m-','y-','k-','w-']
    lenFmt=len(fmt)
    lenEx=0
    oks=0
    params={}
    for pk in pks:
        station=pk1(pk)
        row=data[pk]
        for field in list(row.keys()):
            params[field]=field
        plottingDataAll[station]={"time":[]}
    
        
    for pk in pks:
        plottingData=plottingDataAll[pk1(pk)]
        try:
            t=datetime.datetime.strptime(pk[0][0:-6],defaultTimestampPattern)
        except: 
                #import pdb
                #pdb.set_trace()
            try:
                t=datetime.datetime.strptime(pk[0][0:-1]+".000",defaultTimestampPattern)
            except:
                print("exception pk: ",pk)
        plottingData["time"].append(mdates.date2num(t))
        row=data[pk]
        for field in list(params.keys()):
            if not field.endswith("QualityFlag"):
                v=np.nan
                if field in row:
                    v=row[field]
                    if v=="noData":
                        v=np.nan
                if field in plottingData:
                    plottingData[field].append(v)
                else:
                    plottingData[field]=[v]     
    i=0
    for station in list(plottingDataAll.keys()):
        plottingData=plottingDataAll[station]
        #print len(plottingData["time"])
        if len(plottingData["time"])>0:
            ylabel=""
            for param in list(plottingData.keys()):
                if param!="time":
                    ylabel=param
                    c=fmt[i%lenFmt]
                    plt.plot_date(plottingData["time"], plottingData[param],fmt=c)
                    oks=oks+1
            plt.xlabel('time (s)')
            plt.ylabel(ylabel)
            plt.title(station)
            plt.show()
    #print "number of exceptions: ",lenEx
    #print "number of ok: ",oks
        
        

    
def streamPlotData(data,imageFormat,fmt=None):
    __plotData(data,fmt)
    sio = io.StringIO()
    plt.savefig(sio, format=imageFormat)
    return sio

def displayPlotData(data, fmt=None):
    __plotData(data,fmt)
    plt.show()

