from couchdb.mapping import Document,TextField,DateTimeField, \
IntegerField,BooleanField,ListField,DictField,Mapping
import os.path
import uuid

class LtrNode(Document):
    doctype = TextField()

    name = TextField()
    path = TextField()
    boxname = TextField()
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

    def __init__(self,space=False):
        Document.__init__(self)
        self.space = space

    def new(self):
        self.id = uuid.uuid4().hex
        self.doctype = "node"
        return self

    def updateDrop(self,drop,dryrun=False):
        """ use drop.calcHash, .boxname to update record"""
        self.name = drop.name
        self.mtime = drop.mtime
        self.ftype= drop.ftype
        self.path = drop.path
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
        volpath = os.path.join(self.path,self.name)
        global_files = list(LtrNode.view(self.space.records,"ltrcrawler/children",key=volpath,include_docs=True))
        global_files = filter(lambda n: n.isbox!=True,global_files)
        return map(lambda x: x.connect(self.space),global_files)

    def connect(self,space):
        self.space = space
        return self

    def getVolPath(self):
        if self.path=="/":
            return "/" + self.name
        else:
            return self.path + "/" + self.name

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
        s+= "boxname: %s\n" % self.boxname
        s+= "size: %d\n" % self.size
        s+= "type: %s\n"  % self.ftype
        s+= "mimetype: %s\n" % self.mimetype
        s+= "sha1sum: %s\n" % self.hash
        s+= "present: %s\n" % self.present
        s+= "isbox: %s\n" % self.isbox
        s+= "wanted: %s\n" % self.wanted
        return s


