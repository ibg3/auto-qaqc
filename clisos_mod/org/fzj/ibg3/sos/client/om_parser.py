'''
Created on Apr 2, 2018

@author: sorg
'''

import xml.dom.minidom 
from xml.dom.minidom import Node
import getpass

KNOWN_PRIMARY_KEY_FIELDNAMES=("offering","sample","phenomenontime","samplingtime","time","feature","featureofinterest","urn:ogc:def:phenomenon:ogc:1.0.0:messwertgueltig")

"""
struktur der daten an matlib anpassen
"""

class OmParsedData(object):
    
    def __init__(self,expectedFieldsList):
        self._fields={}
        for f in expectedFieldsList:
            self._fields[f]=(-1,-1,"")
        self._qualifierNames={}
        self._processingStati={}
        self.data={}
        self.__pk=None
            
    def setPrimaryKey(self,primaryKey):
        self.__pk=primaryKey
            
    def setFieldIndex(self,fieldName,idx,unitOfMeasure=""):
        if fieldName in self._fields:
            self._fields[fieldName]=(idx,self._fields[fieldName],unitOfMeasure)
        elif (self.__isQualityField(fieldName)):
            self._fields[fieldName]=(self._fields[fieldName][0],idx)
            
    def __isQualityField(self,fieldName):
        for f in self._fields:
            if fieldName.startswith(f) and fieldName.endswith("QualityFlag"):
                return True
            
    def addData(self, strRow):
        #print ",".join(strRow)
        #print [strRow[self.__pk[i]] for i in self.__pk.keys()]
        self.data[(strRow[self.__pk[i]] for i in list(self.__pk.keys()))]=strRow
    
    def setQualifierNames(self,k,v):
        self._qualifierNames[k]=v
    
    def setProcessingStati(self,k,v):
        self._processingStati[k,v]
        
#     def addData(self,primaryKey,fieldIndex, dataValue):
#         pass

class OmParser(object):

    def __init__(self,o_m_data,omParsedData=None,converter=None, additionalParameters=None):
        if omParsedData==None:
            self._data=OmParsedData()
        else:
            self._data=omParsedData
        
        if converter==None:
            self._converter=OmConverter(self._data)
        else:
            self._converter=converter
            
        self.addOm(o_m_data)
        
    def addOm(self,om):
        try:
            self.__root=xml.dom.minidom.parseString(om)
        except:
            print("can not parse om result: \n"+om)
            raise
        self.__root.normalize()
        self._fields={}
        self._namespaces={"swe":"http://www.opengis.net/swe/1.0.1"}
        self.__extractData(self._data)

    
    def __getPrimarykeyFields(self,fields):  
        result={}
        i=0
        for field in fields:
            fieldName=field.attributes["name"].nodeValue
            if fieldName.lower() in KNOWN_PRIMARY_KEY_FIELDNAMES:
                result[fieldName]=i
        return result
    
    def __getSeparators(self, branch):
        b=self.getElementByName(branch,"swe:encoding")
        b=self.getElementByName(b,"swe:TextBlock")
        if b!=None:
            return (b.getAttribute("decimalSeparator"),b.getAttribute("tokenSeparator"),b.getAttribute("blockSeparator"))
        return None
    
    def _parsingOmHeaderEnd(self):
        pass
    
    def __extractData(self,data):
        members=self.__root.getElementsByTagName("om:member")
        self.__parseMetaOmDataProperty(data)
        for member in members:
            branch=self.getElementByName(member, "om:result")
            fields=self.getElementsByName(branch,"swe:field")
            if fields!=None and len(fields)>0:
                data.setPrimaryKey(self.__getPrimarykeyFields(fields))
                for i in range(0,len(fields)):
                    fieldname=fields[i].attributes["name"].nodeValue
                    suom=""
                    quantity=self.getElementByName(fields[i], "swe:Quantity")
                    if quantity!=None:
                        uom=self.getElementByName(quantity, "swe:uom")
                        if uom!=None:
                            suom=uom.attributes["code"].nodeValue
                    data.setFieldIndex(fieldname,i,suom)
                
                self._parsingOmHeaderEnd()
                 
                values=self.getElementsByName(member,"swe:values")
                svalues=self.getFirstChildData(values[0])
                decimalSeparator,tokenSeparator,blockSeparator=self.__getSeparators(branch)
                rows=svalues.split(blockSeparator)
                for row in rows:
                    if len(row.strip())>0:
                        cells=row.split(tokenSeparator)
                        data.addData(cells)
                        self._converter.convertLines()
                        
    def __parseMetaOmDataProperty(self, data):
        metadataProerties=self.__root.getElementsByTagName("gml:metaDataProperty")
        for metadataProperty in metadataProerties:
            q=False
            fields=self.getElementsByName(metadataProperty, "swe:field")
            indices={}
            tmp={}
            for i in range(0,len(fields)):
                attrName=fields[i].getAttribute("name")
                if attrName!=None:
                    attrName=attrName.lower()
                    tmp[attrName]=i
#                    if attrName in ("qualifierid","genericqualifier","specificqualifier"):
#                        q=True
#                    indices[attrName]=i
            if "genericqualifier" in list(tmp.keys()):
                q=True
                if "id" in tmp:
                    indices["qualifierid"]=tmp["id"]
            else:
                if "id" in tmp:
                    indices["processingstatusid"]=tmp["id"]
                if "processingstatus" in tmp:
                    indices["processingstatuscode"]=i
            indices.update(tmp)
                
            values=self.getElementByName(metadataProperty, "swe:values")
            if values!=None:
                d=self.getFirstChildData(values)
                if d!=None:
                    for row in self.getFirstChildData(values).split(";"):
                        cells=row.split(",")
                        if q:
                            data.setQualifierNames(cells[indices["qualifierid"]],"%s_%s"%(cells[indices["genericqualifier"]],cells[indices["specificqualifier"]]))
                        else:
                            data.setProcessingStati(cells[indices["processingstatusid"]],cells[indices["processingstatuscode"]])
    
    
    
    def __getTimestampFromRasterSosResponse(self,memberNode):
        samplingTime=self.getElementsByName(memberNode,"om:samplingTime")
        if samplingTime!=None:
            timeInstant=self.getFirstChildElement(samplingTime[0])
            if timeInstant!=None:
                timePosition=self.getFirstChildElement(timeInstant)
                if timePosition!=None:
                    return self.getFirstChildData(timePosition)+","
        return ""
             
    def getFirstChildElement(self,parent):
        for child in parent.childNodes:
            if child.nodeType != Node.TEXT_NODE:
                return child
        return None
    
    def getElementsByName(self,branch, nodeName):
        if branch!=None:
            if branch.nodeName==nodeName:
                return [branch]
            else:
                namespace_localname=nodeName.split(":")
                if namespace_localname[0] in self._namespaces:
                    nsuri0=self._namespaces[namespace_localname[0]]
                    nsuri1=branch.namespaceURI
                    if nsuri0==nsuri1:
                        namespace_localname1=branch.nodeName.split(":")
                        if len(namespace_localname1)>1:
                            if namespace_localname[1]==namespace_localname1[1]:
                                return [branch]                
                result=[]
                for child in branch.childNodes:
                    b= self.getElementsByName(child, nodeName)
                    if b!=None and b!=[]:
                        result=result+b
                return result
        return None
    
    def getElementByName(self,branch, nodeName):
        if branch!=None:
            if branch.nodeName==nodeName:
            #if uri+":"+ln==nodeName:
                return branch
            else:
                namespace_localname=nodeName.split(":")
                if namespace_localname[0] in self._namespaces:
                    nsuri0=self._namespaces[namespace_localname[0]]
                    nsuri1=branch.namespaceURI
                    if nsuri0==nsuri1:
                        namespace_localname1=branch.nodeName.split(":")
                        if len(namespace_localname1)>1:
                            if namespace_localname[1]==namespace_localname1[1]:
                                return branch
                for child in branch.childNodes:
                    res=self.getElementByName(child, nodeName)
                    if res!=None:
                        return res
        return None
     
    def getFirstChildData(self,parent):
        for child in parent.childNodes:
            if child.nodeValue!=None:
                if child.nodeValue.strip()!="":
                    return child.nodeValue
        return ""
        
        
                    
class OmConverter(object):
    
    def __init__(self,data):
        self._data=data
        
    def convertLines(self):
        for k in list(self._data.data.keys()):
            print(",".join(self._data.data[k]))
        self._data.data={}
    
    def getHeader(self,fields):
        result=[]
        for field in fields:
            fieldAttributes=self._fields[field]
            s=field
            if len(fieldAttributes)>0:
                s="%s in [%s]"%(s,fieldAttributes[0])
            result.append(s)
        return "%s,%s"%(self._pkHeader,",".join(result))
    
    def isRasterSosResponse(self):
        return self._fields.find("gml:GridCoverage")>0
    
    def getRasterSosHeader(self, member):
        lower=self.getElementsByName(member,"gml:lowerCorner")[0]
        upper=self.getElementsByName(member,"gml:upperCorner")[0]
        bbox="%s,%s"%(self.getFirstChildData(lower).replace(" ", ","),self.getFirstChildData(upper).replace(" ", ","))
        
        srs=lower.attributes["srsName"].nodeValue
        pixels=self.getFirstChildData(self.getElementsByName(member,"gml:high")[0]).split(" ")
        return "bbox: %s;srs: %s;resolution: %s,%s"%(bbox,srs,pixels[0],pixels[1])
    
    def formatRasterSosResponse(self,members,separator=None):
        if members==None:
            members=self.__root.getElementsByTagName("om:member")
        indices={}
        for member in members:
            #fields=self.__root.getElementsByTagName("swe:field")
            fields=self.getElementsByName(member,"swe:field")
            if len(fields)>0:
                numberOfMetadataFields=self.getNumberOfMetadataFields(fields)
                rasterSosTimestamp=self.__getTimestampFromRasterSosResponse(member)
                for i in range(numberOfMetadataFields,len(fields)):
                    fieldname=fields[i].attributes["name"].nodeValue
                    indices[i]=fieldname
                    if fieldname not in self._fields:
                        suom=""
                        quantity=self.getElementByName(fields[i], "swe:Quantity")
                        if quantity!=None:
                            uom=self.getElementByName(quantity, "swe:uom")
                            if uom!=None:
                                suom=uom.attributes["code"].nodeValue
                        self._fields[fieldname]=[suom]
                                
                values=self.getElementsByName(member,"swe:values")
                svalues=self.getFirstChildData(values[0])
                rows=svalues.strip(";").split(";")
                print("#timestamp: %s;%s"%(rasterSosTimestamp.replace(",",""),self.getRasterSosHeader(member)))
                if separator==None:
                    for row in rows:
                        print(row)
                else:
                    for row in rows:
                        pos=row.rfind(",")
                        row=row[0:pos]+separator+row[pos+1:]
                        print(row)
                    
    def qualityAssessment(self):
        self.parseMetaOmDataProperty()
        if len(self._processingStati)>0 and len(self._qualifierNames)>0:
            print("############## PROCESSINGSTATUS ################")
            self.printQualityInfo(self._processingStati)
            print("############## QUALIFIER #######################")
            self.printQualityInfo(self._qualifierNames)
            print("############## QualityFlag SYNTAX ##############")
            print("# PROCESSINGSTATUS_QUALIFIER")
            print("################################################")
    
    def printQualityInfo(self, dikt):
        sorting={}
        for k in list(dikt.keys()):
            sorting[dikt[k]]=k
        keys=list(sorting.keys())
        keys.sort()
        for k in keys:
            print("# %s = %s"%(k,sorting[k]))
   
    
    
