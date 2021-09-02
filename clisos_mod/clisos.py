'''
Created on Aug 2, 2012

@author: sorg
email: j.sorg@fz-juelich.de
'''

import getopt, sys, datetime, io
from clisos_mod.org.fzj.ibg3.sos.client import sosclient, matlibplot_utils
from configparser import ConfigParser
from clisos_mod.org.fzj.ibg3.sos.client.sosclient import GetObservation #, GetCapabilities
from clisos_mod.org.fzj.ibg3.sos.client.sos_result_data_format import getFormatter
from clisos_mod.org.fzj.ibg3.sos.client.getobservation_response import parse as timeSeriesParser
from clisos_mod.org.fzj.ibg3.sos.client.describe_sensor_response import parseSensorMl
from clisos_mod.org.fzj.ibg3.sos.client.getcapabilities_response import parseCapabilities
from symbol import parameters

#using iso-date-format
DATETIME_FORMAT_STRING = "%Y-%m-%dT%H:%M:%S"

def printUsage():
        print("""
    
    usage: python clisos.py OPTION
    
    IBG-3 SOS-Client
    CliSOS is a command line sos-client to request observational data from a OGC compliant 
    sensor observation service (SOS)
    for bug-reports and review send an email to j.sorg@fz-juelich.de
    
    OPTIONS
        --help                                  print this help
    -h, --host=HOST                             hostname/servername (e.g. www.menja.de)
    -p, --port=PORT                             port (e.g. 8080)
    -u, --url=URL                               url/path (e.g. /ibg3sosV1.0/sos
    -P, --get_capabilities                      get the entire capabilities document from the service
    -o, --offering=OFFERING                     specify the offering to use
    -O  --list_offerings                        Get a list of all available Offerings 
    -s, --station=STATION                       specify the station to use
    -Y                                          get all stations (procedures)
    -S                                          get all stations (procedures) from an offering 
    -D                                          get all parameters (observedProperties) from a station
    -L                                          get all parameters (observedProperties) from a Offering
    -X,                                         print station description in xml
    -G, --getData                               get data by a GetObservation-Request
                                                output is csv like with comma separated values
                                                timestamp,featureOfInterest,param0,...,paramN 
                                                (exactly output format depends on sos-output)
                                                output will be written to stdout, therefore use stdout 
                                                forwarding (... > filename) to save output to a file 
    -f, --configfile=FILE                       read/write from/to a configuration file
    -C, --createConfigfileByOffering            create a configuration file for a certain offering 
    -r, --crs=SRS                               spatial reference system to use for entire Request
                                                default is urn:ogc:def:crs:EPSG::4326
    -c, --filter-crs=SRS                        spatial reference system for spatial filter
    -x, --xcoordinate=X                         x-coordinate of Spatial Filter defined by a Point
    -y, --ycoordinate=Y                         y-coordinate of Spatial Filter defined by a Point
    -q                                          proxy hostname
    -w                                          proxy port    
    -j  --responseFormat=CONTENT_TYPE           specify the responseFormat paramter of a SOS 
                                                GetObservation request
    -z  --csvSeparator                          use this character to separate the data values within csv file
    -l  --plot                                  plots the data
    -a  --matlibplot_fmt                        comma separated format (color and symbol) string for the plotting curve
                                                e.g. "g.,r-" the first curve is plotted with green (g) dots (.) and the
                                                second with red (r) lines (-) 
                                                (see http://matplotlib.org/1.3.1/api/pyplot_api.html#matplotlib.pyplot.plot
                                                for more possible format parameters)     
    -b                                          specify a comma separated list of observed properties 
    -d                                          specify a comma separated list of procedures  
    -e                                          specify start and end time stamp separated with semicolon for data retrieval
                                                e.g. 2005-10-13T04:03:14,2007-09-20T16:04:10 
    -g                                          specify a spatial bbox filter. syntax: xmin,ymin,xmax,ymax    
    -i                                          no output when no data is available (else a message about this is returned) 
    -k                                          print no header information (print only data)
    -m                                          print result om document (no parsing, no csv)  
    -n                                          get latest/first data record (0==latest,1==first) 
    -t                                          only count result rows 
    -B                                          providing Bearer-Token
    -M                                          http GET instead of POST (thredds only supports http GET)                               
    """, file=sys.stderr)
    
def printUsageAndExit(errorMessage=""):
    """
    print help message to stderr and exit 
    """
    printWarningAndErrors("\n    error:\n    %s" % (errorMessage,))
    printUsage()
    sys.exit(1)
    
def printWarningAndErrors(message):
    print(message, file=sys.stderr)
    
def checkHostPortUrl(verbose, configFilename, case):
    """
    check if arguments host,port and url are provided from user
    default port: 8080
    default url:  /
    no default for host-> exit program
    """
    if configFilename != None and case != 4:
        offering, parameters, stations, starttime, endtime, srs, spsrs, x, y, model, lhost, lport, lurl, proxyHostname, proxyPort, thematicFilter, responseFormat, csvSeparator, bbox, responseMode, bearer = readConfig(
            configFilename)
        if verbose > 0:
            print("find connection options in config file")
            print("host: " + lhost)
            print("port: " + lport)
            print("url: " + lurl) 
        return (lhost, lport, lurl)

    lport = 8080
    lurl = "/"
    if port != None:
        lport = port
    else:
        printWarningAndErrors("\n    warning:\n    no port is defined - using default port 8080")
    if host == None:
        printUsageAndExit("no hostname defined (-h option)")
    if path != None:
        lurl = path
    else:
        printWarningAndErrors("\n    warning:\n    no path is defined - using default path /")
    return (host, lport, lurl)

def readConfig(configFilename=None, configString=None, timeInterval=[]):
    """
    read configuration-file to get all necessary paramters for a SOS-GetObservation-Request
    returns:
    (offering,parameters,stations,starttime,timeperiod)
    """
    print(configFilename)
    configParser = ConfigParser()
    if configString is not None:
        buf = io.StringIO(configString)
        configParser.read_file(buf)
    elif configFilename is not None:
        configParser.read(configFilename)
    else:
        printUsageAndExit("No Configuration supplied.")

    spatialFilterSrs = "urn:ogc:def:crs:EPSG::31466"
    srs = "EPSG:4326"
    x = y = None
    thematicfilter=[]
    proxyHostname = proxyPort = None
    responseFormat = None
    csvSep=","
    bearer=None
    if configParser.has_option("getObservation", "spatialFilterSrs"):
        spatialFilterSrs = configParser.get("getObservation", "spatialfiltersrs")
    if configParser.has_option("getObservation", "x-coordinate"):
        x = configParser.get("getObservation", "x-coordinate")
    if configParser.has_option("getObservation", "y-coordinate"):
        y = configParser.get("getObservation", "y-coordinate")
    if configParser.has_option("getObservation", "crs"):
        srs = configParser.get("getObservation", "crs")
    if configParser.has_option("getObservation", "responseFormat"):
        responseFormat = configParser.get("getObservation", "responseFormat")
    if configParser.has_option("getObservation", "csvSeperator"):
        csvSep = configParser.get("getObservation", "csvSeperator")
    if configParser.has_option("getObservation", "thematicFilter"):
        s = configParser.get("getObservation", "thematicFilter")
        thematicfilter=s.split(",")
        if verbose>0:
            print("thematic filter: "+",".join(thematicfilter))
        
        
    if configParser.has_option("connection", "proxyHostname"):
        proxyHostname = configParser.get("connection", "proxyHostname")
    if configParser.has_option("connection", "proxyPort"):
        proxyPort = configParser.get("connection", "proxyPort")
    if configParser.has_option("connection", "bearerToken"):
        bearer = configParser.get("connection", "bearerToken")
    
    if configParser.has_option("getObservation", "starttime"):
        starttime=configParser.get("getObservation", "starttime")
    else:
        starttime=None
    if configParser.has_option("getObservation", "endtime"):
        endtime=configParser.get("getObservation", "endtime")
    else:
        endtime=None
    
    bbox=None
    if configParser.has_option("getObservation", "bbox"):
        bbox=configParser.get("getObservation", "bbox").split(",")
        
    responseMode=None
    if configParser.has_option("getObservation", "responseMode"):
        responseMode=configParser.get("getObservation", "responseMode")
        
    
    
    if timeInterval != None and timeInterval!=[]:
            starttime=timeInterval[0]
            endtime=timeInterval[1]
     
    return (configParser.get("getObservation", "offering"),
            configParser.get("getObservation", "parameter"),
            configParser.get("getObservation", "stations"),
            starttime,
            endtime,
            srs,
            spatialFilterSrs,
            x, y,
            configParser.get("getObservation", "resultModel"),
            configParser.get("connection", "host"),
            configParser.get("connection", "port"),
            configParser.get("connection", "url"),
            proxyHostname,
            proxyPort,thematicfilter,responseFormat,csvSep,bbox,responseMode,bearer)


class CliSos(object):

    def __init__(self, resultModel, srs, spatialFilterSrs, config, host, offering, port, procedure, path, xcoordinate, ycoordinate, verbose, proxyHostname, proxyPort, responseFormat, csvSeparator, matlibplot, matlibplot_fmt, preDefObservedProperties, preDefProcs, timeInterval, bbox, noMessageAboutNoData, printNoQualityInfo, printOm, last, onlyCount, bearerToken, method,
                 configString=None):
        self._resultModel = resultModel  
        self._srs = srs
        self._spatialFilterSrs = spatialFilterSrs
        self._configFilename = config
        print(config)
        self._host = host
        self._offering = offering
        self._port = port
        self._procedure = procedure
        self._path = path
        self._xcoordinate = xcoordinate
        self._ycoordinate = ycoordinate
        self._verbose = verbose
        self._proxyHostname = proxyHostname
        self._proxyPort = proxyPort
        self._responseFormat=responseFormat
        self._csvSeparator=csvSeparator
        self._matlibplot=matlibplot
        self._matlibplot_fmt=matlibplot_fmt
        self._preDefObservedProperties=preDefObservedProperties
        self._preDefProcs=preDefProcs
        self._timeInterval=timeInterval
        self._bbox=bbox
        self._noMessageAboutNoData=noMessageAboutNoData
        self._printNoQualityInfo=printNoQualityInfo
        self._printOm=printOm
        self._last=last
        self._onlyCount=onlyCount
        self._bearerToken=bearerToken
        self._method=method

        self._configString = configString


        if int(verbose) > 2:
            print("sensor id: (", self._procedure, ")")
            print("csv separator: ", self._csvSeparator)
        
    def readConfig(self):
        if self._configString is not None and self._configString.strip() != '':
            return self.readConfigString()
        else:
            return self.readConfigFile()


    def readConfigFile(self):
        return readConfig(configFilename=self._configFilename, timeInterval=self._timeInterval)

    def readConfigString(self):
        return readConfig(configString=self._configString, timeInterval=self._timeInterval)

    def checkOffering(self):
        """
        check if an offeringname was set on commandline
        """
        if self._offering == None:
            printUsageAndExit("no offering defined (-o option)")
    
    def checkConfigFilename(self):
        """
        check if an configFilename was set on commandline
        """
        #import pdb
        #pdb.set_trace()
        if self._configFilename == None and self._configString is None:
            printUsageAndExit("no configFilename defined (-f option)")
            
    def checkGetObservationInputs(self, offering, parameters, stations, starttime, endtime):
        """
        check if all necessary parameter for a GetObservation-Request are set in configfile
        parameters and station are optional in configfile 
        """
        if offering == None:
            printUsageAndExit("no offering defined in configfile")
        elif parameters == None:
            parameters = ""
        elif stations == None:
            stations = ""
#        elif starttime == None or starttime.strip() == "":
#            printUsageAndExit("no starttime defined in configfile")
#        elif endtime == None or endtime.strip() == "":
#            printUsageAndExit("no timeperiode defined in configfile")
        return (offering, parameters, stations, starttime, endtime)
    
    def getCapabilities(self, section=None):
        if section is None:
            section = ["OperationsMetadata", "ServiceIdentification", "ServiceProvider", "Filter_Capabilities",
                       "Contents"]
        print(self.__getCapabilities(section).getResponse().read())
        
    def getAllStations(self):
        parseCapabilities(self.__getCapabilities(["OperationsMetadata"]).getResponse().read())
    
    def __getCapabilities(self, sections):
        res = sosclient.GetCapabilities(self._host, self._port, self._path, sections=sections, proxyHost=self._proxyHostname, proxyPort=self._proxyPort,
                                        verbose=self._verbose,bearerToken=bearerToken)
        return res
    
    def listOfferings(self):
        """
        invoke SOS-GetCapabilities-Request and extract available offeringnames
        """
        res = self.__getCapabilities(["Contents"]).getResponse()
        sres = res.read()
        if int(self._verbose) > 2:
            print(sres)
        print("\n".join(sosclient.GetCapabilitiesReponse(sres).getOfferings()))
    
    def getStationsByOffering(self):
        """
        invoke SOS-GetCapabilities-Request and extract all stations (procedures) for a given offeringname
        """
        self.checkOffering()
        res = self.__getCapabilities(["Contents"]).getResponse()
        sres = res.read()
        if int(self._verbose) > 2:
            print(sres)
        print("\n".join(sosclient.GetCapabilitiesReponse(sres).getStationsFromOffering(self._offering)))
    
    def getParameterByOffering(self):
        """
        invoke SOS-GetCapabilities-Request and extract all parameters (phenomenons) for a given offeringname
        """
        self.checkOffering()
        res = self.__getCapabilities(["Contents"]).getResponse()
        print("\n".join(sosclient.GetCapabilitiesReponse(res.read()).getObservedPropertiesFromOffering(self._offering)))
        
    def isRasterSos(self, host, port, url):
        #TODO: nicht noetig, aber der rastersos gibt fuer eine cap-anfrage fuer die einzelenen offerings nicht die richtigen resultmodels zurueck
        #      -> muss in rastersos geaendert werden
        req = self.__getCapabilities(["OperationsMetadata"]) 
        if int(self._verbose) > 0:
            print(req.getRequest())
        res = req.getResponse().read()
        if int(self._verbose) > 1:
            print(res)
        return res.find("om:TimeSeriesObservation") >= 0
        
    def createConfigfile(self):
        """
        create a configuration-file depending on an offering to hold all necessary parameters for 
        a SOS-GetObservation-Request
        """
        self.checkOffering()
        self.checkConfigFilename()
        res = self.__getCapabilities(["Contents"]).getResponse()
        sres = res.read()
        if int(self._verbose) > 1:
            print(sres)
        response = sosclient.GetCapabilitiesReponse(sres)
        obsProps = response.getObservedPropertiesFromOffering(self._offering)
        if len(self._preDefObservedProperties)>0:
            obsProps2=[]
            for op in self._preDefObservedProperties:
                if op in obsProps:
                    obsProps2.append(op)
            if len(obsProps2)>0:
                obsProps=obsProps2
        procs = response.getStationsFromOffering(self._offering)
        if len(self._preDefProcs)>0:
            procs2=[]
            for op in self._preDefProcs:
                if op in procs:
                    procs2.append(op)
            if len(procs2)>0:
                procs=procs2
                
        configParser = ConfigParser()
        configParser.add_section("getObservation")
        configParser.add_section("connection")
        configParser.set("getObservation", "offering", self._offering)
        configParser.set("getObservation", "stations", ",".join(procs))
        configParser.set("getObservation", "parameter", ",".join(obsProps))
        if self._xcoordinate != None:
            configParser.set("getObservation", "x-coordinate", self._xcoordinate)
        if self._ycoordinate != None:
            configParser.set("getObservation", "y-coordinate", self._ycoordinate)
        resultModel = "om:Observation"
        if self.isRasterSos(self._host, self._port, self._path):
            resultModel = "om:TimeSeriesObservation"
        configParser.set("getObservation", "resultModel", resultModel)
        now = datetime.datetime.now()
        twoDays = datetime.timedelta(days=1)
        configParser.set("getObservation", "starttime", (now - twoDays).strftime(DATETIME_FORMAT_STRING))
        configParser.set("getObservation", "endtime", now.strftime(DATETIME_FORMAT_STRING))
        if self._spatialFilterSrs != None:
            configParser.set("getObservation", "spatialFilterSrs", self._spatialFilterSrs)
        if self._srs != None:
            configParser.set("getObservation", "crs", self._srs)
        configParser.set("connection", "host", self._host)
        configParser.set("connection", "port", self._port)
        configParser.set("connection", "url", self._path)
        if self._proxyHostname != None:
            configParser.set("connection", "proxyHostname", self._proxyHostname)
        if self._proxyPort != None:
            configParser.set("connection", "proxyPort", self._proxyPort)
        f = open(configFilename, "w")
        configParser.write(f)
    
    def getObservation(self):
        """
        read configuration-file to get all necessary parameters for invoking a SOS-GetObservation-Request
        sos-response will be parsed and a comma-separated file (csv) is created and written to stdout 
        """
        if self._offering==None or self._preDefObservedProperties==None or self._preDefProcs==None:
            self.checkConfigFilename()
            offering, parameters, stations, starttime, endtime, srs, spsrs, x, y, model, host, port, url, proxyHostname, proxyPort, thematicFilter, self._responseFormat, self._csvSeparator, self._bbox, self._responseMode, bearer = self.readConfig()
            offering, parameters, stations, starttime, endtime = self.checkGetObservationInputs(offering, parameters, stations, starttime, endtime)
        else:
            offering=self._offering
            parameters=",".join(self._preDefObservedProperties)
            stations=",".join(self._preDefProcs)
            host=self._host
            port=self._port
            url=self._path
            starttime=None
            endtime=None
            if timeInterval != None and timeInterval!=[]:
                starttime=timeInterval[0]
                endtime=timeInterval[1]
            srs=self._srs
            spsrs=None
            x=None
            y=None
            model="om:Observation"
            proxyHostname=None
            proxyPort=None
            thematicFilter=None
            self._responseMode= None
            #model = "om:Observation"
        if self._bearerToken==None:
            self._bearerToken=bearer
            
#        st=etime=None
#        if starttime!=None:
#            st = datetime.datetime.strptime(starttime, DATETIME_FORMAT_STRING)
#        if endtime!=None:
#            etime = datetime.datetime.strptime(endtime, DATETIME_FORMAT_STRING)
        if int(self._verbose) > 0:
            print("host: %s\nport: %s\npath: %s\noffering: %s\nparameter: %s\nstations: %s\nstarttime: %s\nendtime: %s\nsrs: %s\nfiler-srs: %s\nx: %s\ny: %s\nresultModel: %s\n" % \
                  (host, port, url, offering, parameters, stations, starttime, endtime, srs, spsrs, x, y, model))
        #p=parameters.replace("[", "").replace("]", "").split(",")
        p=parameters.split(",")
        getObs = GetObservation(host, port, url, offering, starttime,#.strftime(DATETIME_FORMAT_STRING),
                             endtime,#.strftime(DATETIME_FORMAT_STRING),
                             #stations.replace("[", "").replace("]", "").split(","),
                             stations.split(","),
                             p,
                             srs="urn:ogc:def:crs:%s" % (srs,),
                             spatialFilterSrs="urn:ogc:def:crs:%s" % (spsrs,), x=x, y=y, resultModel=model,
                             proxyHost=proxyHostname, proxyPort=proxyPort, verbose=self._verbose, responseFormat=self._responseFormat, thematicFilter=thematicFilter,
#                             bbox=self._bbox,last=self._last, responseMode=self._responseMode, bearerToken=bearerToken)
                             bbox=self._bbox,last=self._last, responseMode=self._responseMode, bearerToken=self._bearerToken, method=self._method)
        if int(self._verbose) > 1:
            print(getObs.getRequest())
        res = getObs.getResponse()
        om = res.read().decode("UTF-8")
        sendMail=True
        if self._onlyCount:
            import xml.dom.minidom 
            from clisos_mod.org.fzj.ibg3.xml.xml_utils import getFirstChildData,getElementByName
            root=xml.dom.minidom.parseString(om)
            branch=getElementByName(root, "om:result")
            branch=getElementByName(branch, "swe:Count")
            branch=getElementByName(branch, "swe:value")
            #v=getFirstChildElement(branch)
            print(getFirstChildData(branch))  
        elif self._printOm:
            print(om)
        else:
            if int(self._verbose) > 2:
                print(om)
                print("csv separator: ",self._csvSeparator)
            self.checkGetObservationReponse(om)
            if model == "om:TimeSeriesObservation":
                timeSeriesParser(om)
            elif self._responseMode=='out-of-band':
                formatter=getFormatter(om, "wms")
                formatter.formatData()  
            else:
                formatter=getFormatter(om, "csv")
                if self._matlibplot:
                    data=formatter.extractData()
                    if int(self._verbose)>2:
                        print("from om extracted data: ", data)
                        try:
                            f=open("/home/sorg/clisos.om.extracted.data.json","w")
    #                        import pickle
    #                        pickle.dump(data,f)
                            import json
                            json.dump(data,f)
                            f.close()
                        except:
                            pass
                    matlibplot_utils.displayPlotData(data,self._matlibplot_fmt)
                    sendMail=False
                else:
                    res= formatter.formatData(self._csvSeparator,len(p),not self._printNoQualityInfo)
                    if res!="":
                        if not res.startswith("no data available") or not self._noMessageAboutNoData:
                            return res

        #sendTextMail()
        
    def runGetOBservationInBatchMode(self):
        pass
        
    def getResponsibleOfStation(self):
        res = self.__describeSensor()
        sres = res.read()
        self.checkGetObservationReponse(sres)
        "".find("sml:email")
        
    
#    def _sendTextEMail(self,sender,receiver,text,subject):
#        mail = getToolByName(self, 'MailHost')
#        if mail!=None:
#            textMail = MIMEText(text, 'plain')
#            textMail['Subject'] = subject
#            textMail['From'] = sender
#            textMail['To'] = ', '.join([receiver,"tsmjuelich@gmail.com","j.sorg@fz-juelich.de"])
#            mail.send(textMail.as_string())
 
            
    def checkGetObservationReponse(self, response):
        if response.find("ExceptionReport") >= 0:
            printUsageAndExit(response)
    
    
    
        
    def __describeSensor(self):
        return sosclient.DescribeSensor(self._host, self._port, self._path, self._procedure, proxyHost=self._proxyHostname, proxyPort=self._proxyPort,
                                       verbose=self._verbose,bearerToken=self._bearerToken, method=self._method).getResponse()
            
    def getParameterByStation(self):
        """
        get parameter (phenomenons) for which data is available on the Sensor Observation Service (SOS)
        a SOS-DescribeSensor-Request is invoked to get the information 
        """
        res = self.__describeSensor()
        parseSensorMl(res.read(), printOutputs=True)
    
    def printSensorMl(self):
        """
        get a description for a given station
        a SOS-DescribeSensor-Request is invoked to get the information  
        """
        res = self.__describeSensor()
        sres = res.read()
        self.checkGetObservationReponse(sres)
        print(sres)
        
if __name__ == "__main__":  
    
    try:
        #all possible commandline-arguments
        #see man getopt for detailed description
        opts, args = getopt.getopt(sys.argv[1:], "c:CDf:Gh:LOo:p:r:Ss:u:Xx:y:q:w:Pj:z:la:b:d:e:g:ikmYn:t:B:M",
                                   ["help", "port=", "url=", "host=" , "list_offerings=", "stationsByOffering=",
                                    "parameterByOffering=", "getData", "configfile=",
                                    "createConfigfileByOffering=", "srs=", "parameterByStation=", "printSensorMl=",
                                    "printStationCoordinate", "spatialFilterSrs", "spatialFilterPoint", "resultModel", "v", "vv", "vvv",
                                    "proxyHost=", "proxyPort=", "get_capabilities","responseFormat=","csvSeparator=","plot","matlibplot_fmt"])
    except getopt.GetoptError as err:
        #if something goes wrong print error message and exit
        printUsageAndExit(str(err))
    
    #no switch-case in python
    case = -1
    #global (used in subroutines) variables
    resultModel = "om:Observation"
    srs = None
    spatialFilterSrs = None
    configFilename = None
    host = None
    offering = None
    port = None
    procedure = None
    path = None
    xcoordinate = None
    ycoordinate = None
    #debug level
    verbose = 0
    proxyHostname = None
    proxyPort = None
    matlibplot= False
    #change
    #author: juergen sorg
    #date: 2013-10-11
    responseFormat=None
    csvSeparator=","
    matlibplot_fmt=None
    preDefObservedProperties=[]
    preDefProcs=[]
    timeInterval=[]
    bbox=[]
    noMessageAboutNoData=False
    printNoQualityInfo=False
    printOm=False
    last=None
    onlyCount=False
    bearerToken = None
    method="POST"
    
    
    #loop over all commandline-options
    for o, a in opts:
        if o == "--help":
            printUsage()
            exit(0)
        elif o == "-m":
            printOm=True
        elif o == "-r":
            srs = a
        elif o == "-c":
            spatialFilterSrs = a
        elif o == "-f":
            configFilename = a
        elif o == "-h":
            host = a
        elif o == "-o":
            offering = a
        elif o == "-p":
            port = a
        elif o == "-s":
            procedure = a
        elif o == "-u":
            path = a
        elif o == "-x":
            xcoordinate = a
        elif o == "-y":
            ycoordinate = a
        elif o == "-C":
            case = 4
        elif o == "-D":
            case = 5
        elif o == "-G":
            case = 3
        elif o == "-L":
            case = 2
        elif o == "-O":
            case = 0
        elif o == "-S":
            case = 1
        elif o == "-X":
            case = 6
        elif o == "-P":
            case = 7
        elif o == "--v":
            verbose = 1
        elif o == "--vv":
            verbose = 2
        elif o == "--vvv":
            verbose = 3
        elif o == "-q":
            proxyHostname = a
        elif o == "-w":
            proxyPort = a
        elif o == "-j":
            responseFormat = a
        elif o == "-z":
            csvSeparator = a
        elif o == "-l":
            matlibplot = True
        elif o == "-a":
            matlibplot_fmt= a
        elif o == "-b":
            preDefObservedProperties=a.split(",")
        elif o == "-d":
            preDefProcs=a.split(",")
        elif o == "-e":
            timeInterval=a.split(",")
        elif o == "-g":
            bbox=a.split(",")
        elif o == "-i":
            noMessageAboutNoData=True
        elif o == "-k":
            printNoQualityInfo=True
        elif o == "-Y":
            case = 8
        elif o == "-n":
            last = a
        elif o == "-t":
            onlyCount=True
        elif o == "-B":
            bearerToken = a
        elif o == "-M":
            method="GET"
            
    
    #check for necessary commandline-arguments
    if not case == 3:
        host, port, path = checkHostPortUrl(verbose, configFilename, case)
    
    cliSos = CliSos(resultModel, srs, spatialFilterSrs, configFilename, host, offering, port, procedure, path, xcoordinate, ycoordinate, verbose, proxyHostname, proxyPort, responseFormat, csvSeparator, matlibplot, matlibplot_fmt, preDefObservedProperties, preDefProcs, timeInterval, bbox, noMessageAboutNoData, printNoQualityInfo, printOm, last, onlyCount, bearerToken,method)
    #python-switch 
    {
    0: cliSos.listOfferings,
    1: cliSos.getStationsByOffering,
    2: cliSos.getParameterByOffering,
    3: cliSos.getObservation,
    4: cliSos.createConfigfile,
    5: cliSos.getParameterByStation,
    6: cliSos.printSensorMl,
    7: cliSos.getCapabilities,
    8: cliSos.getAllStations
    }.get(case, printUsage)()
