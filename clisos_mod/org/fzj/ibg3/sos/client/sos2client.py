'''
Created on Jul 16, 2018

@author: sorg
'''

from owslib.sos import SensorObservationService
from owslib.swe.observation.sos200 import SOSGetObservationResponse
from owslib.etree import etree
#from owslib.swe.observation.sos200.SensorObservationService_2_0_0 import get_observation
#from owslib.swe.common import TimeRange

class Sos:
    def __init__(self, host, port, url, offering=None, fromTimestamp=None, toTimestamp=None, procedures=[], phenomenons=[],
                 srs=None,proxyHost=None, proxyPort=None, proxyUrl=None):
        self.service = SensorObservationService("http://"+host+":"+str(port)+url,version='2.0.0')

    def getOfferings(self):
        return self.service.contents
    
    def getObservation(self, responseFormat="http://www.opengis.net/om/2.0",
                        offerings=None,
                        observedProperties=None,
                        eventTime=None,
                        procedure=None,**kwargs):
        return self.service.get_observation(
                        responseFormat=responseFormat,
                        offerings=offerings,
                        observedProperties=observedProperties,
                        eventTime=eventTime,
                        procedure=procedure,**kwargs)
        
    def getContent(self):
        print(list(self.service.__dict__.keys()))
        print("\n".join(self.service.observed_properties))
        print(list(self.service.contents.keys()))
        for off in list(self.service.contents.keys()):
            print(type(off))
            print(self.service.contents[off])
            print(type(self.service.contents[off]))
            print(list(self.service.contents[off].__dict__.keys()))

        return sorted(self.service.contents)
    
    def getObservedPropertiesFromOffering(self,offeringName):
        return self.service.contents[offeringName].observed_properties
    
    def getStationsFromOffering(self,offeringName):
        return self.service.contents[offeringName].procedures
    
    def getSensorMl(self,procedure, procedureDescriptionFormat="http://www.opengis.net/sensorML/2.0.0"):
        return self.service.describe_sensor(outputFormat=procedureDescriptionFormat, procedure=procedure)
         
sos=Sos("ibg3wradar.ibg.kfa-juelich.de",8080,"/sample.public.sos2/service")
print(sos.getObservedPropertiesFromOffering("WU_AW_014"))
print(sos.getOfferings())
print(sos.getStationsFromOffering("WU_AW_014"))
print(sos.getSensorMl("WU_AW_014"))
print(sos.getSensorMl("WU_AW_014", procedureDescriptionFormat="http://www.opengis.net/sensorML/1.0.1"))
getObsResp= sos.getObservation("http://www.opengis.net/om/2.0", ["WU_AW_014",], ['StreamWaterSmpConcentrationDOC',], procedure="WU_AW_014")
getObsResp= sos.getObservation("http://www.opengis.net/om/2.0", ["WU_AW_014",], ['StreamWaterSmpConcentrationDOC',], procedure="WU_AW_014", MergeObservationsIntoDataArray=True)
parsedOm=SOSGetObservationResponse(etree.fromstring(getObsResp))
ts=parsedOm.observations[0]
print(type(ts))
res=ts.get_result()
print(type(res))
print(list(res.__dict__.keys()))
print(res)

ts=parsedOm.observations[1]
print(type(ts))
res=ts.get_result()
print(type(res))
print(list(res.__dict__.keys()))
print(res)

# for offContent in sos.getContent():
#     print type(offContent)
#     print type(offContent.keys())