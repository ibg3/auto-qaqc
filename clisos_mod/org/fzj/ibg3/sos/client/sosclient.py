'''
Created on Jul 30, 2012

@author: sorg
'''

import http.client,io
import xml.dom.minidom
from owslib.sos import SensorObservationService
#from clisos_mod.org.fzj.ibg3.sos.client.sos2client import getObsResp
#from clisos import verbose

host = "ibg3wradar.ibg.kfa-juelich.de"
port = 8080


DEFAULT_SRS="urn:ogc:def:crs:EPSG::4326"
GAUSS_KRUGER_SRS="urn:ogc:def:crs:EPSG::31466"

DESCRIBE_SENSOR_TEMPLATE="""<?xml version="1.0" encoding="UTF-8"?>
<DescribeSensor version="1.0.0" service="SOS"
    xmlns="http://www.opengis.net/sos/1.0"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.opengis.net/sos/1.0
    http://schemas.opengis.net/sos/1.0.0/sosDescribeSensor.xsd"
    outputFormat="text/xml;subtype=&quot;sensorML/1.0.1&quot;">
    
    <procedure>%s</procedure>
    
</DescribeSensor>
"""

eventtimeLastestFirst="""
  <eventTime>
    <ogc:TM_Equals>
      <ogc:PropertyName>om:samplingTime</ogc:PropertyName>
      <gml:TimeInstant>
        <gml:timePosition>%s</gml:timePosition>
      </gml:TimeInstant>
    </ogc:TM_Equals>
  </eventTime>
"""

eventtimeDuring="""
  <eventTime>
    <ogc:TM_During>
      <ogc:PropertyName>om:samplingTime</ogc:PropertyName>
      <gml:TimePeriod>
        <gml:beginPosition>%s</gml:beginPosition>
        <gml:endPosition>%s</gml:endPosition>
      </gml:TimePeriod>
    </ogc:TM_During>
  </eventTime>
"""

MARKER={"srs":0,"offering":1,"begin":2,"end":3,"procedures":4,"observedProperties":5,"spatialFilter":6,"resultModel":7}
REQUEST_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<GetObservation xmlns="http://www.opengis.net/sos/1.0"
  xmlns:ows="http://www.opengis.net/ows/1.1"
  xmlns:gml="http://www.opengis.net/gml"
  xmlns:ogc="http://www.opengis.net/ogc"
  xmlns:om="http://www.opengis.net/om/1.0"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.opengis.net/sos/1.0
  http://schemas.opengis.net/sos/1.0.0/sosGetObservation.xsd"
  service="SOS" version="1.0.0" srsName="%s">
  
  <offering>%s</offering>
  
  %s
  %s
  %s
  %s
  %s
  <responseFormat>%s</responseFormat>
  <resultModel>%s</resultModel>
  <responseMode>%s</responseMode>

</GetObservation>"""

"""<responseMode>inline</responseMode>"""

SPATIAL_FILTER_TEMPLATE="""
<featureOfInterest>
   <ogc:Intersects>
      <ogc:PropertyName>urn:ogc:data:location</ogc:PropertyName>
      <gml:Point srsName="%s">
         <gml:pos>%s %s</gml:pos>
      </gml:Point>
   </ogc:Intersects>
</featureOfInterest>"""

SPATIAL_FILTER_BBOX_TEMPLATE="""
<featureOfInterest>
   <ogc:BBOX>
      <ogc:PropertyName>urn:ogc:data:location</ogc:PropertyName>
      <gml:Envelope srsName="%s">
        <gml:lowerCorner>%s %s</gml:lowerCorner>
        <gml:upperCorner>%s %s</gml:upperCorner>
      </gml:Envelope>
    </ogc:BBOX>
</featureOfInterest>"""


THEMATIC_FILTER_TEMPLATE="""
  <result>
    <ogc:PropertyIsGreaterThan>
      <ogc:PropertyName>%s</ogc:PropertyName>
      <ogc:Literal>%s</ogc:Literal>
    </ogc:PropertyIsGreaterThan>
  </result>
"""

GET_CAPABILITIES_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<GetCapabilities xmlns="http://www.opengis.net/sos/1.0"
  xmlns:ows="http://www.opengis.net/ows/1.1"
  xmlns:ogc="http://www.opengis.net/ogc"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.opengis.net/sos/1.0
  http://schemas.opengis.net/sos/1.0.0/sosGetCapabilities.xsd"
  service="SOS">
  
  <ows:AcceptVersions>
    <ows:Version>1.0.0</ows:Version>
  </ows:AcceptVersions>
  
  <ows:Sections>  
    %s
  </ows:Sections>

</GetCapabilities>"""


TODO = """OperationsMetadata</ows:Section>  
    <ows:Section>ServiceIdentification</ows:Section>
    <ows:Section>ServiceProvider</ows:Section>
    <ows:Section>Filter_Capabilities</ows:Section>
    <ows:Section>Contents</ows:Section>
"""
TAG_CAP_SECTION = "<ows:Section>%s</ows:Section>"
TAG_PROC = "<procedure>%s</procedure>"
TAG_PHENOMENON = "<observedProperty>%s</observedProperty>"

HOST="localhost"
PORT=8080
URL="/ibg3sosV1.0/sos"

import logging

def enableHttpVerbosity():
    try:
        import http.client as http_client
    except ImportError:
        # Python 2
        import http.client as http_client
    http_client.HTTPConnection.debuglevel = 1
    
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True

class SosRequest(object):
    
    def __init__(self,host,port,url,proxyHost=None, proxyPort=None, proxyUrl=None,
                 verbose=0, bearerToken=None, tls=False, method="POST"):
        
        if proxyHost!=None:
            self._host=proxyHost
            self._port=proxyPort
            self._url="http://%s:%s%s"%(host,port,url)
        else:
            self._host = host
            self._port = port
            self._url = url
                
        self._proxyHost=proxyHost
        self._proxyPort=proxyPort
        self._proxyUrl=proxyUrl
        self._verbose=verbose
        self._tls=tls
        self._bearerToken=bearerToken
        self._method=method
        
        if method!="POST":
            self.sos = SensorObservationService("https://"+self._host+":"+str(self._port)+self._url,version='1.0.0')
            if int(verbose) > 0:
                enableHttpVerbosity()  
        
    def getRequest(self):
        return self._request
    
    def getResponse(self):
        if int(self._verbose) > 0:
            print("server-url: http://%s:%s%s"%(self._host,self._port,self._url))   
        if self._port == "443" or self._tls:
            con = http.client.HTTPConnection(self._host, self._port)
        else:
            con = http.client.HTTPConnection(self._host, self._port)
        #print self.getRequest()
        headers = None
        if self._bearerToken is None:
            headers = {"Content-type":"application/xml"}
        else:
            headers = {"Content-type":"application/xml", "Authorization":"Bearer "+self._bearerToken}
        con.request("POST", self._url, self.getRequest(), headers)
        res=con.getresponse()
        self._status=res.status
        if int(self._verbose) > 0:
            print("response-status: %s"%(self._status,))
        return res
    
    def _removeTailSlash(self, url):
        if(url!=None):
            if(url.endswith("/")):
                return url[0:-1]
        return url 
    
class GetObservation(SosRequest):
    
    def __init__(self, host, port, url, offering, fromTimestamp, toTimestamp, procedures=[], phenomenons=[],
                 srs=None,spatialFilterSrs=GAUSS_KRUGER_SRS,x=None,y=None,resultModel="om:Observation", 
                 proxyHost=None, proxyPort=None, proxyUrl=None,
                 verbose=0,responseFormat=None, thematicFilter=None, bbox=None, last=None, responseMode='inline', bearerToken=None, method="POST"):
        super(GetObservation, self).__init__(host,port,url,proxyHost,proxyPort,proxyUrl,verbose,bearerToken=bearerToken, method=method)
        if method!="POST":
            self._offering=offering;
            self._start=fromTimestamp;
            self._end=toTimestamp
            self._procedures=procedures
            self._obsProps=phenomenons
            self._resultModel=resultModel
            self._responseFormat=responseFormat
            self._request=""
        else:        
            self._setVariablesInTemplate(offering, fromTimestamp, toTimestamp, procedures, phenomenons,resultModel,x,y,spatialFilterSrs, responseFormat, thematicFilter, bbox, last, responseMode, srs)
        
    def _setVariablesInTemplate(self, offering, fromTimestamp, toTimestamp, procedures, phenomenons, resultModel, x, y, spatialFilterSrs, responseFormat, thematicFilter, bbox, last, responseMode, srs):
        self._srs = DEFAULT_SRS
        if srs != None:
            self._srs = srs
        spatailFilter = ""
        # if(resultModel!="om:Observation"):
        if responseFormat == None:
            responseFormat = "text/xml;subtype=&quot;om/1.0.0&quot;"
        if(x != None and y != None and spatialFilterSrs != None):
            spatailFilter = SPATIAL_FILTER_TEMPLATE % (spatialFilterSrs, x, y)
        if(bbox != None and bbox != [] and spatialFilterSrs != None):
            spatailFilter = SPATIAL_FILTER_BBOX_TEMPLATE % (spatialFilterSrs, bbox[0], bbox[1], bbox[2], bbox[3])

        sThematicFilter = ""
        if(thematicFilter != None and thematicFilter != []):
            sThematicFilter = THEMATIC_FILTER_TEMPLATE % (thematicFilter[0], thematicFilter[1])
        procSection = ""
        if len(procedures) > 0 :
            if len(procedures) != 1 or procedures[0] != "": 
                procSection = "\n".join([TAG_PROC % (proc.strip(),) for proc in procedures])
        phenSection = ""
        if len(phenomenons) > 0:
            phenSection = "\n".join([TAG_PHENOMENON % (phen.strip(),) for phen in phenomenons])
        if last != None:
            if self._verbose > 0:
                print("latest/first: " + last)
            eventtime = eventtimeLastestFirst % ({0:"latest", 1:"first"}.get(int(last)),)
        elif fromTimestamp == None or toTimestamp == None:
            eventtime = ""
        else:
            eventtime = eventtimeDuring % (fromTimestamp, toTimestamp)
        if(responseMode == None):
            responseMode = "inline"
        self._request = REQUEST_TEMPLATE % (self._srs, offering, eventtime,
                                        procSection,
                                        phenSection,
                                        spatailFilter, sThematicFilter,
                                        responseFormat,
                                        resultModel, responseMode)
        
    def getResponse(self):
        if self._method=="POST":
            return super(GetObservation, self).getResponse()   
        resp=self.sos.get_observation(responseFormat='text/xml;subtype="om/1.0.0"',
                                     offerings=[self._offering],
                                           observedProperties=self._obsProps,
                                           procedure=self._procedures[0],
                                           eventTime=self._start+"/"+self._end,
                                           # MergeObservationsIntoDataArray=True,
                                           timeout=6000)
        return io.StringIO(resp)


        
class GetObservation2(GetObservation):
    
    def __init__(self, host, port, url, offering, fromTimestamp, toTimestamp, procedures=[], phenomenons=[],
                 srs=None,spatialFilterSrs=GAUSS_KRUGER_SRS,x=None,y=None,resultModel="om:Observation", 
                 proxyHost=None, proxyPort=None, proxyUrl=None,
                 verbose=0,responseFormat=None, thematicFilter=None, bbox=None, last=None, responseMode='inline', batchStep="yearly"):
        super(GetObservation, self).__init__(host,port,url,proxyHost,proxyPort,proxyUrl,verbose)
        self._setVariablesInTemplate(offering, "%s", "%s", procedures, phenomenons,resultModel,x,y,spatialFilterSrs, responseFormat, thematicFilter, bbox, last, responseMode, srs)
        self.__fromTimeStamp=fromTimestamp
        self.__toTimeStamp=toTimestamp
        self.__batchStep=batchStep
        
    def getResponse(self):
        """
        TODO: batch mode (e.g. in yearly pieces)
        default: time interval > 2 years -> download data in 1 year steps
        cmd switches: -b [1m|1y(default)|14d]
        """
        import datetime
        start=datetime.datetime.strptime(self.__fromTimeStamp)
        end=datetime.datetime.strptime(self.__toTimeStamp)
        delta=datetime.timedelta(year=1)
        while True:
            stepEnd=start+delta
            
            if stepEnd>=end:
                break
        return GetObservation.getResponse(self)

    
class GetCapabilities(SosRequest):
    
    def __init__(self, host, port, url,proxyHost=None, proxyPort=None, proxyUrl=None, sections=["Contents"],
                 verbose=0,bearerToken=None):
#        self._host = host
#        self._port = port
#        self._url = url
        super(GetCapabilities, self).__init__(host,port,url,proxyHost,proxyPort,proxyUrl,verbose=verbose,bearerToken=bearerToken)
        self._request = GET_CAPABILITIES_TEMPLATE % ("\n".join([TAG_CAP_SECTION % (section,) for section in sections]),)
        if verbose>1:
            print(self._request)
        
class DescribeSensor(SosRequest):
    
    def __init__(self, host, port, url, sensor,  proxyHost=None, proxyPort=None, proxyUrl=None,
                 verbose=0,bearerToken=None, method="POST"):
        super(DescribeSensor, self).__init__(host,port,url,proxyHost,proxyPort,proxyUrl,verbose=verbose,bearerToken=bearerToken,method=method)
        if method=="POST":
            self._request = DESCRIBE_SENSOR_TEMPLATE % (sensor,)
            if verbose>1:
                print(self._request)
        else:
            self._request=sensor
            
    def getResponse(self):
        if self._method=="POST":
            return super(DescribeSensor, self).getResponse()    
        
        #getObsOp = sos.get_operation_by_name('getobservation')
        resp=self.sos.describe_sensor(procedure=self._request,
                                      outputFormat='text/xml;subtype="sensorML/1.0.1/profiles/ioos_sos/1.0"')
        return io.StringIO(resp)
            
    


class GetCapabilitiesReponse(object):
    
    def __init__(self,xml):
        #print xml
        self._xml=xml
        self._parse()
        
    def _parse(self):
        root=xml.dom.minidom.parseString(self._xml)
        self._offeringsWithStationsAndPhenomenons={}
        offeringElements=root.getElementsByTagName("sos:ObservationOffering")
        for offeringElement in offeringElements:
            procedures=[]
            observedProperties=[]
            name=offeringElement.getAttribute("gml:id")
            for child in offeringElement.childNodes:
                #child=xml.dom.minidom.Element()
                if child.nodeName=="gml:name" and child.getAttribute("codeSpace")!=None and child.getAttribute("codeSpace")=='uniqueID':
                    #pass#name=str(xml_utils.getFirstChildData(child))
                    from clisos_mod.org.fzj.ibg3.xml import xml_utils
                    name=str(xml_utils.getFirstChildData(child))
                elif child.nodeName=="sos:procedure":
                    if child.getAttribute("xlink:href")!=None:
                        #procedures.append(str(child.getAttribute("xlink:href")))
                        procedures.append(child.getAttribute("xlink:href"))
                elif child.nodeName=="sos:observedProperty":
                    if child.getAttribute("xlink:href")!=None:
                        #observedProperties.append(str(child.getAttribute("xlink:href")))
                        observedProperties.append(child.getAttribute("xlink:href"))
            self._offeringsWithStationsAndPhenomenons[name]=(procedures,observedProperties)
            
    def getObservedPropertiesFromOffering(self,offeringName):
        obsProp=self._offeringsWithStationsAndPhenomenons.get(offeringName,[])
        if len(obsProp)>1:
            return obsProp[1]
    
    def getStationsFromOffering(self,offeringName):
        phens=self._offeringsWithStationsAndPhenomenons.get(offeringName,[])
        if len(phens)>0:
            return phens[0]
        
    def getOfferings(self):
        return list(self._offeringsWithStationsAndPhenomenons.keys())
        
            
        
    
