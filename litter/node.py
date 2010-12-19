from couchdb.mapping import *

import uuid

class LtrNode(Document):
    doctype = TextField()
    name = TextField()
    parent = TextField()
    meta = DictField(Mapping.build(
        ftype = TextField(),
        hash = TextField(),
        mtime = IntegerField(),
        size = IntegerField()
        ))
    delta = ListField( DictField(Mapping.build(
        boxid = TextField(),
        ftype = TextField(),
        hash = TextField(),
        mtime = IntegerField(),
        size = IntegerField()
        )) 
    )
    present = ListField( TextField())

    def __init__(self,parentobj=False,space=False):
        Document.__init__(self)
        self.parentobj = parentobj
        self.space = space

    def connect(self,space,parentobj=None):
        self.parentobj = parentobj
        self.space = space
        return self
    def getParentObj(self):
        return self.parentobj

    def new(self,parent):
        self.id = uuid.uuid4().hex
        self.doctype = "node"
        self.parent = parent
        return self

    def updateDrop(self,drop,dryrun=False):
        """ use drop.calcHash, .boxid to update record"""
        self.name = drop.name
        self.meta.mtime = drop.mtime
        self.meta.ftype= drop.ftype
        self.meta.size= drop.size
        if dryrun:
            self.meta.hash = ""
            self.meta.mimetype = ""
        else:
            self.meta.hash = drop.calcHash()
            self.meta.mimetype = drop.calcMime()
        self.delta = []
        
    def children(self):
        if self.space == False:
            return []
        global_files = list(LtrNode.view(self.space.records,"ltrcrawler/children",key=self.id,include_docs=True))
        return map(lambda x: x.connect(self.space,self),global_files)

    def diff(self,drop):
        """ compare mtime, size etc """
#        import sys,pprint
#        sys.exit(0)
        diffs = []
        for attr in drop.features:
            (a,b) = (self.meta[attr],getattr(drop,attr))
            if a != b:
                diffs.append((attr,a,b))

        return diffs

    def stat(self):
        s= "File: %s\n" % self.volpath
        s+= "size: %d\n" % self.meta.size
        s+= "type: %s\n"  % self.meta.ftype
        s+= "mimetype: %s\n" % self.meta.mime
        s+= "drops: %s\n" % self.present
        return s


