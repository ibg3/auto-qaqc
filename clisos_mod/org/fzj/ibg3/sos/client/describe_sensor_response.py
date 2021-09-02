'''
Created on Aug 1, 2012

@author: sorg
'''
import xml.sax
from xml.sax import ContentHandler

def parseSensorMl(response,printOutputs=False, printCoordinates=False):
    #parser = xml.sax.make_parser()
    #parser.setContentHandler(OMParser())
    #print parser.__dict__.keys()
    xml.sax.parseString(response,SensorMlParser(printOutputs, printCoordinates))

class SensorMlParser(ContentHandler):
    
    def __init__(self,printOutputs=False, printCoordinates=False):
        self._printOutputs=printOutputs
        self._printCoordinates=printCoordinates
        
    isOutput=False
    isPosition=False
    isCoordinateValue=False
    def characters(self, content):
        if SensorMlParser.isCoordinateValue and self._printCoordinates:
            print(content)
            SensorMlParser.isCoordinateValue=False
        return ContentHandler.characters(self, content)
    
    def startElement(self, name, attrs):
        if self._printOutputs:
            if name=="sml:output":
                SensorMlParser.isOutput=True
            elif SensorMlParser.isOutput:
                if name=="swe:Quantity":
                    try:
                        print(attrs.get("definition"))
                    except:
                        print(type(attrs.get("definition")))
        elif self._printCoordinates:
            if name=="sml:position":
                SensorMlParser.isPosition=True
            elif SensorMlParser.isPosition:
                if name=="swe:Position":
                    print(attrs.get("referenceFrame"))
                elif name=="swe:value":
                    SensorMlParser.isCoordinateValue=True
                
        return ContentHandler.startElement(self, name, attrs)


    def endElement(self, name):
        if name=="sml:output":
            SensorMlParser.isOutput=False
        return ContentHandler.endElement(self, name)
    
    
