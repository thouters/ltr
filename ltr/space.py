import couchdb

views = {
    'boxes': { 'map': "function(doc) { if (doc.doctype == \"box\") emit(doc._id,doc); }"},
    'hashes': { 'map': "function(doc) { if (doc.doctype == \"node\" && doc.meta.hash) emit(doc.meta.hash, doc); }" },
    'by-path': { 'map': "function(doc) { if (doc.doctype == \"node\") emit(doc.path, doc); }"},
    'dirs': { 'map':  "function(doc) { if (doc.doctype == \"node\" && doc.ftype==\"dir\") emit(doc.path+\"/\"+doc.name, doc); }" },
}



class LtrSpace:
    name = False
    records = False
    context = False
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
        self.records.update([couchdb.Document(_id='_design/ltrcrawler', language='javascript', views=views)])
        self.fromUri(context)

    def fromUri(self,context):
        self.context = context
        self.name = self.context.spacename
        self.records = self.context.getCursor()[self.name]

    def getBoxUri(self,name):
        return self.context.spaceuri+name
