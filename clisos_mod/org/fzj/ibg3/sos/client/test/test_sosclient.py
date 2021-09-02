'''
Created on Jul 30, 2012

@author: sorg
'''

import unittest, datetime
from clisos_mod.org.fzj.ibg3.sos.client.sosclient import GetCapabilities,GetObservation,DescribeSensor,GetObservation2
from clisos_mod.org.fzj.ibg3.sos.client import sos_result_data_format

HOST="localhost"
PORT=8080
URL="/ibg3sosV1.0/sos"

class TestSosClient(unittest.TestCase):
    
    def testGetObservation(self):
        req=GetObservation(HOST,PORT,URL,"Soil",
               datetime.datetime.now(), datetime.datetime.now(), #+datetime.timedelta(minute=1),
               ["proc0", "proc1", "proc2", "proc3", ],
               ["phen0", "phen1", "phen2", "phen3", ]).getRequest()
        self.assertEqual(True, req.find("<observedProperty>phen2</observedProperty>")>0)
        
        getObs=GetObservation(HOST,PORT,URL,"Soil",
               datetime.datetime(2012,7,1).isoformat(), datetime.datetime.now().isoformat(), #+datetime.timedelta(minute=1),
               ['RU_BK_003', 'RU_BK_002'],
               ['urn:ogc:def:phenomenon:OGC:1.0.30:WaterContentSoil50cmAveraged', 
                'urn:ogc:def:phenomenon:OGC:1.0.30:WaterContentSoil5cmSensor2'])
        res=getObs.getResponse()
        #getobservation_response.parse(res.read())
        sos_result_data_format.getFormatter(res.read(), "csv")  
        #print csv.formatData()
        #self.assertEqual(True, req.find("<observedProperty>phen2</observedProperty>")>0)
        
        
    def testGetCapabilities(self):
        getCapObj=GetCapabilities(HOST,PORT,URL,["Contents","ServiceProvider"])
        req=getCapObj.getRequest()
        self.assertEqual(True, req.find("<ows:Section>Contents</ows:Section>")>0)
        res=getCapObj.getResponse().read()
#        print res
        self.assertEqual(True,res.find('<sos:procedure xlink:href="RU_CR_004"/>')>=0)
#        print GetCapabilitiesReponse(res).getStationsFromOffering("Soil") 
#        print GetCapabilitiesReponse(res).getObservedPropertiesFromOffering("Soil") 
        
    def testDescribeSensor(self):
        res= DescribeSensor(HOST,PORT,URL,"RU_BK_001").getResponse().read()
        #print res
        from clisos_mod.org.fzj.ibg3.sos.client.describe_sensor_response import parseSensorMl
        parseSensorMl(res,False,True)
        
    def testHasattr(self):
        pass
    
    def testTimeseriesRequest(self):
        getObs=GetObservation("ibg3wradar.ibg.kfa-juelich.de",8080,"/ibg3rastersos/sos","Reflectivity",
               datetime.datetime(2012,8,30).isoformat(), datetime.datetime.now().isoformat(),
               phenomenons=['urn:ogc:def:phenomenon:OGC:1.0.30:Reflectivity',],
               spatialFilterPoint=(5706719.299312554, 2550407.925887833),resultModel="om:TimeSeriesObservation")
        print(getObs.getRequest())
        res=getObs.getResponse()
        response=res.read()
        from clisos_mod.org.fzj.ibg3.sos.client.getobservation_response import parse
        parse(response)
        
    def testGetObservationBatch(self):
        getObs=GetObservation2(host, port, url, offering, fromTimestamp, toTimestamp, procedures, phenomenons, srs, spatialFilterSrs, x, y, resultModel, proxyHost, proxyPort, proxyUrl, verbose, responseFormat, thematicFilter, bbox, last, responseMode)
    
    
        
        

