from org.fzj.ibg3.algo.cosmicray_station_processing import execute
from orig_data import msg
from clisos_mod.clisos import CliSos

msg={}
def clisos():
    # config_string = "".join(map(chr, list(map(int, msg["payload"]["data"]))))
    config_string = '''[getObservation]
offering = Public
resultmodel = om:Observation
stations = RU_C_006
parameter = NeutronCount_Epithermal_Cum1hr,AirPressure_1m
starttime = 2012-09-01T00:00:00
endtime = 2013-08-01T00:00:00

[connection]
host = ibg3wradar.ibg.kfa-juelich.de
port = 8080
url = /eifelrur_public/sos'''

    print(config_string)
    msg['clisos_config_string'] = config_string
    resultModel = "om:Observation"
    srs = None
    spatialFilterSrs = None
    host = None
    offering = None
    port = None
    procedure = None
    path = None
    xcoordinate = None
    ycoordinate = None
    # debug level
    proxyHostname = None
    proxyPort = None
    matlibplot = False
    # change
    # author: juergen sorg
    # date: 2013-10-11
    responseFormat = None
    csvSeparator = ","
    matlibplot_fmt = None
    preDefObservedProperties = []
    preDefProcs = []
    timeInterval = []
    bbox = []
    noMessageAboutNoData = False
    printNoQualityInfo = False
    printOm = False
    last = None
    onlyCount = False
    bearerToken = None

    # configFilename = "/home/t.korf/PycharmProjects/clisos/data/local/data.cfg"
    configFilename = None
    # configString = None
    verbose = "2"
    method = "POST"

    sos = CliSos(resultModel, srs, spatialFilterSrs, configFilename, host, offering, port, procedure, path,
                 xcoordinate, ycoordinate, verbose, proxyHostname, proxyPort, responseFormat, csvSeparator,
                 matlibplot, matlibplot_fmt, preDefObservedProperties, preDefProcs, timeInterval, bbox,
                 noMessageAboutNoData, printNoQualityInfo, printOm, last, onlyCount, bearerToken, method,
                 configString=config_string)

    s = sos.getObservation()


    f = open("orig_data_RU_C_006_2012.txt", "a")
    f.write(s)
    f.close()

#    f = open("payload.txt", "a")
#    f.write(out)
#    f.close()

    #f = open("header.txt", "a")
    #f.write(header)
    #f.close()

#    f = open("config.txt", "a")
#    f.write(config_string)
#    f.close()

    return msg

clisos()
