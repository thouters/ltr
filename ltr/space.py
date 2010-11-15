import couchdb

views = {
    'boxes': { 'map': open("views/boxes/map.js").read() },
    'hashes': { 'map': open("views/hashes/map.js").read() },
    'by-path': { 'map': open("views/by-path/map.js").read() },
    'dirs': { 'map':  open("views/dirs/map.js").read() },
}

class LtrSpace:
    name = False
    records = False
    uri = False
    def newFromUri(self,uri):
        self.uri = uri
        self.name = uri.spacename
        cursor = self.uri.getCursor()
        if self.name in cursor:
            print "ltr: drop old database ", self.name
            del cursor[self.name]
        print "ltr: create database ", self.name
        cursor.create(self.name)
        print "ltr: push design docs ", self.name
        self.records.update([couchdb.Document(_id='_design/ltrcrawler', language='javascript', views=views)])
        self.fromUri(uri)

    def fromUri(self,uri):
        self.uri = uri
        self.name = self.uri.spacename
        self.records = self.uri.getCursor()[self.name]
