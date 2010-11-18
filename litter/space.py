import couchdb

views = {
    'boxes': { 'map': "function(doc) { if (doc.doctype == \"box\") emit(doc._id,doc); }"},
    'by-hash': { 'map': "function(doc) { if (doc.doctype == \"node\" && doc.meta.hash) emit(doc.meta.hash, doc); }" },
    'by-parent': { 'map': "function(doc) { if (doc.doctype == \"node\") emit(doc.parent, doc); }"},
    'tree': { 'map':  "function(doc) { if (doc.doctype == \"node\" && doc.meta.ftype==\"dir\") emit(doc.meta.path, doc); }" },
    'dirs': { 'map':  "function(doc) { if (doc.doctype == \"node\" && doc.meta.ftype==\"dir\") emit(doc); }" },
}



class LtrSpace:
    def __init__(self):
        self.name = False
        self.records = False
        self.context = False
        self.boxes = []

    def newFromUri(self,context):
        self.context = context
        self.name = context.spacename
        cursor = self.context.getCursor()
        if self.name in cursor:
            print "ltr: drop old database ", self.name
            del cursor[self.name]
        print "ltr: create database ", self.name
        cursor.create(self.name)
        print "ltr: push design docs ", self.name
        self.records = self.context.getCursor()[self.name]
        self.records.update([couchdb.Document(_id='_design/ltrcrawler', language='javascript', views=views)])
        self.records.update([{"_id":"ROOT"}])
        self.fromUri(context)

    def fromUri(self,context):
        self.context = context
        self.name = self.context.spacename
        self.records = self.context.getCursor()[self.name]

    def getBoxUri(self,name):
        return self.context.spaceuri+name
