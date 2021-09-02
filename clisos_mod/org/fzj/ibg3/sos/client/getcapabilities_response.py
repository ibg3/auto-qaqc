'''
Created on May 31, 2016

@author: sorg
'''
import xml.sax,sys
from xml.sax import ContentHandler

def parseCapabilities(response):
    xml.sax.parseString(response,CapabilitiesParser())

class CapabilitiesParser(ContentHandler):
    
    def __init__(self):
        self.printProcedures=True
        self._isProc=False
        self._printNow=False
        self._isGetObsParams=False
        
    def _print(self, txt="\n"):
        sys.stdout.write(txt)
        sys.stdout.flush()


    def characters(self, content): 
        if self._printNow and content!=None and content.strip()!="":
            self._print(content.strip())
            self._print()
            
        return ContentHandler.characters(self, content)
    
    def startElement(self, name, attrs):
        nameAttr=attrs.get("name")
        if name!=None and name=="ows:Operation":
            if nameAttr=="GetObservation":
                self._isGetObsParams=True
        elif self._isGetObsParams and name=="ows:Parameter" and nameAttr=="procedure": 
            self._isProc=True
        elif self._isProc and name=="ows:Value":
            self._printNow=True
            self._isProc=False
            self._isGetObsParams=False
        return ContentHandler.startElement(self, name, attrs)
    
    def endElement(self, name):
        if name=="ows:AllowedValues":
            self._printNow=False
        ContentHandler.endElement(self, name)
        

