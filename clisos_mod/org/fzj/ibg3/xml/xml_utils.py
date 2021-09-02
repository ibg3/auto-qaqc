'''
Created on Aug 1, 2012

@author: sorg
'''

from xml.dom.minidom import Node 

#def getFirstChildElement(parent):
#    for child in parent.childNodes:
#        if child.nodeType != Node.TEXT_NODE:
#            return child
#    return None
#
#def getElementsByName(branch, nodeName):
#    if branch != None:
#        if branch.nodeName == nodeName:
#            return [branch]
#        else:
#            result = []
#            for child in branch.childNodes:
#                b = getElementsByName(child, nodeName)
#                if b != None and b != []:
#                    result = result + b
#            return result
#    return None
#
#def getElementByName(branch, nodeName):
#    if branch != None:
#        if branch.nodeName == nodeName:
#            return branch
#        else:
#            for child in branch.childNodes:
#                if getElementByName(child, nodeName) != None:
#                    return child
#    return None
# 
#def getFirstChildData(parent):
#    for child in parent.childNodes:
#        if child.nodeValue != None:
#            if child.nodeValue.strip() != "":
#                return child.nodeValue
#    return ""
#
#
def getFirstChildElement(parent):
        for child in parent.childNodes:
            if child.nodeType != Node.TEXT_NODE:
                return child
        return None
   
def getElementsByName(branch, nodeName):
    if branch!=None:
        if branch.nodeName==nodeName:
            return [branch]
        else:
            result=[]
            for child in branch.childNodes:
                b= getElementsByName(child, nodeName)
                if b!=None and b!=[]:
                    result=result+b
            return result
    return None

def getElementByName(branch, nodeName):
    if branch!=None:
        if branch.nodeName==nodeName:
            return branch
        else:
            for child in branch.childNodes:
                res=getElementByName(child, nodeName)
                if res!=None:
                    return res
    return None
 
def getFirstChildData(parent):
    for child in parent.childNodes:
        if child.nodeValue!=None:
            if child.nodeValue.strip()!="":
                return child.nodeValue
    return ""

#def getAllContentOfElementAsDict(doc,elem):
#    d=Document()
#    nl=d.getElementsByTagName(elem)
#    res={}
#    for n in nl.childNodes:
#        n=Node()
#        v=getFirstChildData(n)
#        if v!="":
            

