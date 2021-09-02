'''
Created on Oct 5, 2011

@author: sorg
'''
import functools

import xml.dom.minidom
from xml.dom.minidom import Node

def comp(tuple1,tuple2):
    if len(tuple1)==1:
        if tuple1[0]==tuple2[0]:
            return 0
        elif tuple1[0]>tuple2[0]:
            return 1
        return -1 
    if tuple1[1]>tuple2[1]:
        return 1
    elif tuple1[1]==tuple2[1]:
        if tuple1[0]>tuple2[0]:
            return 1
        elif tuple1[0]==tuple2[0]:
            return 0
    return -1
    

def getFormatter(o_m_data,format=None, additionalParameters=None):
    switch={
            "csv": Sos2Csv,
            "wms": Sos2Wms
           }
    return switch.get(format,OmFormatter)(o_m_data,additionalParameters)

class OmFormatter(object):
    def __init__(self,o_m_data,additionalParameters=None):
        self._fields=o_m_data
        
    def formatData(self):
        return self._fields
    
class Sos2Wms(OmFormatter):
    def __init__(self,o_m_data,additionalParameters=None):
        self._data=o_m_data
        try:
            self.__root=xml.dom.minidom.parseString(o_m_data)
        except:
            print("can not parse om result: \n"+o_m_data)
            raise
        self.__root.normalize()
        
    def formatData(self):
        results=self.__root.getElementsByTagName("om:result")
        if results!=None:
            for r in results:
                print(r.attributes["xlink:href"].nodeValue)

class Sos2Csv(object):
    def __init__(self,o_m_data,additionalParameters=None):
        self._numberOfMetadataFields=None
        self._data=o_m_data
        try:
            self.__root=xml.dom.minidom.parseString(o_m_data)
        except:
            print("can not parse om result: \n"+o_m_data)
            raise
        self.__root.normalize()
        self._fields={}
        self._qualifierNames={}
        self._processingStati={}
        self._namespaces={"swe":"http://www.opengis.net/swe/1.0.1"}

    def getNumberOfMetadataFields(self,fields):  
        if self._numberOfMetadataFields==None:  
            self._numberOfMetadataFields=0
            f=[]
            for field in fields:
                f.append(field.attributes["name"].nodeValue)
                if field.attributes["name"].nodeValue.lower()=="offering":
                    self._numberOfMetadataFields=self._numberOfMetadataFields+1
                elif field.attributes["name"].nodeValue.lower()=="sample":
                    self._numberOfMetadataFields=self._numberOfMetadataFields+1
                elif field.attributes["name"].nodeValue.lower()=="phenomenontime":
                    self._numberOfMetadataFields=self._numberOfMetadataFields+1
                elif field.attributes["name"].nodeValue.lower()=="samplingtime":
                    self._numberOfMetadataFields=self._numberOfMetadataFields+1
                elif field.attributes["name"].nodeValue.lower()=="time":
                    self._numberOfMetadataFields=self._numberOfMetadataFields+1
                elif field.attributes["name"].nodeValue.lower()=="feature":
                    self._numberOfMetadataFields=self._numberOfMetadataFields+1
                elif field.attributes["name"].nodeValue.lower()=="featureofinterest":
                    self._numberOfMetadataFields=self._numberOfMetadataFields+1
                elif field.attributes["name"].nodeValue.lower()=="urn:ogc:def:phenomenon:ogc:1.0.0:messwertgueltig":
                    self._numberOfMetadataFields=self._numberOfMetadataFields+1
            self._pkHeader=",".join(f[0:self._numberOfMetadataFields])
        return self._numberOfMetadataFields
    
    def getPrimaryKey(self,row):
        return tuple(row[0:self._numberOfMetadataFields])
#        sPk=[]
#        for i in range(0,self._numberOfMetadataFields):
#            sPk.append(row[i])
#        return "|".join(sPk)

    def getSeparators(self, branch):
        b=self.getElementByName(branch,"swe:encoding")
        b=self.getElementByName(b,"swe:TextBlock")
        if b!=None:
            return (b.getAttribute("decimalSeparator"),b.getAttribute("tokenSeparator"),b.getAttribute("blockSeparator"))
        return None
    
    def extractData(self,separator=None,members=None):
        if members==None:
            members=self.__root.getElementsByTagName("om:member")
        data={}
        indices={}
        for member in members:
            #fields=self.__root.getElementsByTagName("swe:field")
            branch=self.getElementByName(member, "om:result")
            fields=self.getElementsByName(branch,"swe:field")
            if fields!=None and len(fields)>0:
            #if fields!=None:
                numberOfMetadataFields=self.getNumberOfMetadataFields(fields)
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
                decimalSeparator,tokenSeparator,blockSeparator=self.getSeparators(branch)
                rows=svalues.split(blockSeparator)
                for row in rows:
                    if len(row.strip())>0:
                        cells=row.split(tokenSeparator)
                        pk=self.getPrimaryKey(cells)
                        data_row={}
                        if pk in data:
                            data_row=data.get(pk)
                        for col_idx in range(numberOfMetadataFields,len(cells)):   
                            col_name=indices[col_idx]
                            data_row[col_name]=cells[col_idx]
                            col_idx=col_idx+1
                        data[pk]=data_row
        return data
    
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
        return self._data.find("gml:GridCoverage")>0
    
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
                    
        
    
    def formatData(self,separator=",",numberOfParametersRequested=1, printHeader=False):
        members=self.__root.getElementsByTagName("om:member")
        #import pdb
        #pdb.set_trace()
        if printHeader:
            self.qualityAssessment()
        if False:#numberOfParametersRequested<=1 or len(members)<=1:
            # formatData2 is faster and more memory friendly (but usable only for single station request/responses
            return self.formatData2(members,separator)
        elif self.isRasterSosResponse():
            self.formatRasterSosResponse(members,separator)
            return ""
        else:
            data=self.extractData(separator)
            if type(data)==dict:
                #result=u"no data available for the given parameter(s)"
                if len(data)>0:
                    result=[]
                    sortedFields=sorted(self._fields.keys())
                    for pk in sorted(list(data.keys()), key=functools.cmp_to_key(comp)):

                        row=[]
                        row.append(",".join(pk))
                        data_row=data[pk]
                        for field in sortedFields:
                            value="nodata"
                            if field in data_row:
                                value=str(data_row[field])
                            row.append(value)
                        result.append(",".join(row))
                    if len(result)>0:
                        if printHeader:
                            return "#%s\n%s"%(self.getHeader(sortedFields), "\n".join(result))
                        return "\n".join(result)
                return "no data available for the given parameter(s)"
    
    def formatData2(self,members,separator=None):
        b=True
        result="no data available for the given parameter(s)"
        for member in members:
            #fields=self.__root.getElementsByTagName("swe:field")
            rasterSosTimestamp=self.__getTimestampFromRasterSosResponse(member)
            fields=self.getElementsByName(member,"swe:field")
            numberOfMetadataFields=self.getNumberOfMetadataFields(fields)
            values=self.getElementsByName(member,"swe:values")
            if b:
                b=False
                if len(fields)>2:
                    result=" , ".join(fields[i].attributes["name"].nodeValue for i in range(0,numberOfMetadataFields))
                    for i in range(numberOfMetadataFields,len(fields)):
                        suom=""
                        quantity=self.getElementByName(fields[i], "swe:Quantity")
                        if quantity!=None:
                            uom=self.getElementByName(quantity, "swe:uom")
                            if uom!=None:
                                suom=uom.attributes["code"].nodeValue
                            rasterSosTimestamp=""
                        result="%s , %s in [%s]"%(result,fields[i].attributes["name"].nodeValue,suom)
                    result="# %s"%(result,)
                elif len(values)>0:
                    result=""
                else:
                    result="no data available for the given parameter(s)"
            rows=""
            if len(values)>0:
                svalues=self.getFirstChildData(values[0])
                rows="%s%s"%(rasterSosTimestamp,svalues.replace(";", "\n").strip())
                if separator!=None:
                    rows=rows.replace(",", separator);
            if result!=None:
                result="%s\n%s"%(result,rows)
        return result.encode("utf-8")
    
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
    
    def parseMetaOmDataProperty(self):
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
                            self._qualifierNames[cells[indices["qualifierid"]]]="%s_%s"%(cells[indices["genericqualifier"]],cells[indices["specificqualifier"]])
                        else:
                            self._processingStati[cells[indices["processingstatusid"]]]=cells[indices["processingstatuscode"]]
#            if len(fields)==3:
#                for i in range(0,len(fields)):
#                    attrName=fields[i].getAttribute("name")
#                    if attrName!=None:
#                        fieldIndices[{"qualifierid":  0,"genericqualifier": 1,"specificqualifier": 2}[attrName.lower()]]=i
#                values=self.getElementByName(metadataProperty, "swe:values")
#                for row in self.getFirstChildData(values).split(";"):
#                    cells=row.split(",")
#                    self._qualifierNames[cells[fieldIndices[0]]]="%s_%s"%(cells[fieldIndices[1]],cells[fieldIndices[2]])
#            elif len(fields)==2:
#                for i in range(0,len(fields)):
#                    attrName=fields[i].getAttribute("name")
#                    if attrName!=None:
#                        fieldIndices[{"processingstatusid":  0,"processingstatus": 1, "processingstatusdesc":2}[attrName.lower()]]=i
#                values=self.getElementByName(metadataProperty, "swe:values")
#                for row in self.getFirstChildData(values).split(";"):
#                    cells=row.split(",")
#                    self._processingStati[cells[fieldIndices[0]]]=cells[fieldIndices[1]]

