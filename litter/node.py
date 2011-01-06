from couchdb.mapping import Document,TextField,DateTimeField, \
IntegerField,BooleanField,ListField,DictField,Mapping
import os.path
import uuid

class LtrNode(Document):
    doctype = TextField()

    name = TextField()
    path = TextField()
    parent = TextField()
    boxid = TextField()
    addtime = DateTimeField()

    ftype = TextField()
    hash = TextField()
    mimetype = TextField()
    ctime = DateTimeField()
    mtime = IntegerField()
    size = IntegerField()

    isbox = BooleanField()
    present = ListField(TextField())
    wanted = BooleanField()

    log = ListField(DictField(Mapping.build(  \
                            dt = DateTimeField(),
                            etype = TextField(),
                            old = TextField(),
                            new = TextField() )))

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
        self.mtime = drop.mtime
        self.ftype= drop.ftype
        if drop.ftype=="dir":
            self.path = drop.volpath
        self.size= drop.size
        if dryrun:
            self.hash = ""
            self.mimetype = ""
        else:
            self.hash = drop.calcHash()
            self.mimetype = drop.calcMime()
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
        if self.path:
            return self.path
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
            (a,b) = (getattr(self,attr),getattr(drop,attr))
            if a != b:
                diffs.append((attr,a,b))

        return diffs

    def stat(self):
        s= "File: %s\n" % self.getVolPath()
        s+= "inode: %s\n" % self.id
        s+= "boxid: %s\n" % self.boxid
        s+= "size: %d\n" % self.size
        s+= "type: %s\n"  % self.ftype
        s+= "mimetype: %s\n" % self.mimetype
        s+= "sha1sum: %s\n" % self.hash
        s+= "present: %s\n" % self.present
        s+= "isbox: %s\n" % self.isbox
        s+= "wanted: %s\n" % self.wanted
        return s


