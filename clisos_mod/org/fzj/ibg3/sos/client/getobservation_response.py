'''
Created on Aug 1, 2012

@author: sorg
'''
import xml.sax
from xml.sax import ContentHandler

def parse(response):
    #parser = xml.sax.make_parser()
    #parser.setContentHandler(OMParser())
    #print parser.__dict__.keys()
    xml.sax.parseString(response,OMParser())

class OMParser(ContentHandler):
    def characters(self, content):
        if hasattr(self, "isTimeseriesObservationValue") and self.isTimeseriesObservationValue:
            self.value=content
        elif hasattr(self, "timePosition") and self.timePosition and hasattr(self, "value"):
            print("%s,%s"%(content,self.value,))
#            
#        if hasattr(self, "_isValuesElement") and self._isValuesElement:
#            print content
        return ContentHandler.characters(self, content)
    
    def startElement(self, name, attrs):
        if name=="ns:CV_TimeInstantValuePair":
            self.timeseriesObservation=True
        elif hasattr(self, "timeseriesObservation") and self.timeseriesObservation and name=="ns:value":
            self.isTimeseriesObservationValue=True
        elif hasattr(self, "timeseriesObservation") and self.timeseriesObservation and name=="gml:timePosition":
            self.timePosition=True
#        if name=="swe:values":
#            self._isValuesElement=True
        return ContentHandler.startElement(self, name, attrs)


    def endElement(self, name):
        #self._isValuesElement=False
        if name=="ns:CV_TimeInstantValuePair":
            self.timeseriesObservation=False
        elif hasattr(self, "timeseriesObservation") and self.timeseriesObservation and name=="ns:value":
            self.isTimeseriesObservationValue=False
        elif hasattr(self, "timePosition") and self.timePosition and name=="gml:timePosition":
            self.timePosition=False
        return ContentHandler.endElement(self, name)
    
    
