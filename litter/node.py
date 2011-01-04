from couchdb.mapping import *
import os.path

import uuid

class LtrNode(Document):
    doctype = TextField()
    name = TextField()
    parent = TextField()
    meta = DictField(Mapping.build(
        path = TextField(),
        ftype = TextField(),
        hash = TextField(),
        mimetype = TextField(),
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
    wanted = ListField( TextField())

    def __init__(self,parentobj=False,space=False):
        Document.__init__(self)
        self.parentobj = parentobj
        self.space = space


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
        if drop.ftype=="dir":
            self.meta.path = drop.volpath
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

    def connect(self,space,parentobj=False):
        self.parentobj = parentobj
        self.space = space
        return self

    def getVolPath(self):
        if "path" in self.meta:
            return self.meta.path
        else:
            if self.parentobj == False:
                return "/"
            else:
                return os.path.join(self.parentobj.getVolPath(),self.name)

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
        s= "File: %s\n" % self.getVolPath()
        s+= "size: %d\n" % self.meta.size
        s+= "type: %s\n"  % self.meta.ftype
        s+= "mimetype: %s\n" % self.meta.mimetype
        s+= "drops: %s\n" % self.present
        s+= "wanted: %s\n" % self.wanted
        return s


