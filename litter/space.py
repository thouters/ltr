import couchdb
from uri import LtrUri
from box import LtrBox
from node import LtrNode
import os
from os.path import isfile

views = {
    'boxes': { 'map': "function(doc) { if (doc.doctype == \"box\") emit(doc._id,doc); }"},
    'by-hash': { 'map': "function(doc) { if (doc.doctype == \"node\" && doc.hash) emit(doc.hash, doc); }" },
    'children': { 'map': "function(doc) { if (doc.doctype == \"node\") emit(doc.path, doc._id); }"},
    'path': { 'map': "function(doc) { if (doc.doctype == \"node\") emit([doc.path, doc.name],null); }"},
    'tree': { 'map':  "function(doc) { if (doc.doctype == \"node\" && doc.ftype==\"dir\") emit(doc.path); }" },
}

class LtrCookieException(Exception):
    pass

class LtrSpace(LtrUri):
    def __init__(self):
        self.name = False
        self.records = False
        self.dbcursor = False

    def createfromUri(self,uri):
        LtrUri.setUri(self,uri)
        self.name = self.spacename
        cursor = self.getCursor()
        if self.name in cursor:
            print "ltr: drop old database ", self.name
            del cursor[self.name]
        print "ltr: create database ", self.name
        cursor.create(self.name)
        print "ltr: push design docs ", self.name
        self.records = self.getCursor()[self.name]
        self.records.update([couchdb.Document(_id='_design/ltrcrawler', language='javascript', views=views)])
        return self

    def setUri(self,uri):
        LtrUri.setUri(self,uri)
        self.name = self.spacename
        if self.name in self.getCursor():
            self.records = self.getCursor()[self.name]
        return self

    def getBoxUri(self,name):
        return self.spaceuri+name

    def connectDatabaseServer(self):
        #print "ltr: connect", self.dbserveruri
        self.dbcursor = couchdb.Server(self.dbserveruri)

    def getCursor(self):
        if not self.dbcursor:
            self.connectDatabaseServer()
        return self.dbcursor

    def getBox(self,boxname):
        return LtrBox.load(self.records,boxname).setSpace(self)

    def getBoxNames(self):
        return map(lambda x: x.setSpace(self).id,list(LtrBox.view(self.records,"ltrcrawler/boxes")))

    @classmethod
    def boxFromCookie(cls,path,space=False):
        #find cookie
        boxroot = path 
        while len(boxroot)>1:
            testfile = os.path.join(boxroot,".ltr") 
            if isfile(testfile):
                break
            boxroot = os.path.dirname(boxroot)

        if len("/") == len(boxroot):
            raise LtrCookieException("directory not in litter dropbox: %s"%path)

        f = open(testfile,'r')
        c = f.read().strip()
        f.close()

        if space==False:
            space = LtrSpace().setUri(c)
        uri = LtrUri().setUri(c)
        box = space.getBox(uri.boxname)

        cwd = path[len(boxroot):]
        if cwd == "":
            cwd = "/"
        box.cwd = cwd
        box.fspath = boxroot
        return box

    def setopt(self,key,value):
        (docname,keyname)=key.split(".")
        d = LtrBox.load(self.records,docname)
        setattr(d,keyname,value)
        d.store(self.records)

