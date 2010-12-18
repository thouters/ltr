import couchdb
from uri import LtrUri
from box import LtrBox
import os
from os.path import isfile

views = {
    'boxes': { 'map': "function(doc) { if (doc.doctype == \"box\") emit(doc._id,doc); }"},
    'by-hash': { 'map': "function(doc) { if (doc.doctype == \"node\" && doc.meta.hash) emit(doc.meta.hash, doc); }" },
    'children': { 'map': "function(doc) { if (doc.doctype == \"node\") emit(doc.parent, doc._id); }"},
    'path': { 'map': "function(doc) { if (doc.doctype == \"node\") emit([doc.parent, doc.name],null); }"},
    'tree': { 'map':  "function(doc) { if (doc.doctype == \"node\" && doc.meta.ftype==\"dir\") emit(doc.meta.path, doc._id); }" },
}

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
        self.records.update([{"_id":"ROOT"}])
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
        print "ltr: connect", self.dbserveruri
        self.dbcursor = couchdb.Server(self.dbserveruri)

    def getCursor(self):
        if not self.dbcursor:
            self.connectDatabaseServer()
        return self.dbcursor

    def getBox(self,boxname):
        return LtrBox.load(self.records,boxname).setSpace(self)

    @classmethod
    def fromCookie(cls,path,space=False):
        #find cookie
        testpath = path 
        while len(testpath)>1:
            testfile = os.path.join(testpath,".ltr") 
            if isfile(testfile):
                break
            testpath = os.path.dirname(testpath)
        if len(testpath) == 1:
            raise LtrCookieException("directory not in litter dropbox: %s"%path)

        f = open(testfile,'r')
        c = f.read().strip()
        f.close()

        if space==False:
            space = LtrSpace().setUri(c)
        uri = LtrUri().setUri(c)
        box = space.getBox(uri.boxname)

        box.cwd = path[len(testpath):]
        box.setPath(testpath)
        return box

