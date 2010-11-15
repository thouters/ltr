import os
import uuid
from .drop import LtrBoxRoot
from .space import LtrSpace
from .context import LtrContext

class LtrBox:
    record = False
    name = False
    rootnode = False
    space = False
    context = False
    uri=False

    def __init__(self,space=False):
        self.space = space

    def fromUri(self,context):
        self.context = context
        self.space = LtrSpace()
        self.space.fromUri(context)
        self.getRecord()

    def newFromUri(self,context):
        if not self.space:
            s = LtrSpace()
            self.context = context
            s.newFromUri(self.context)
            self.space = s
        self.name = context.boxname
        self.uri = context.boxuri
        self.new()

    def new(self):
        self.record = {}
        self.record["_id"] = self.name
        self.record["doctype"] = "box"
        self.space.records.update([self.record])

    def getRecord(self):
        self.record = self.space.records[self.context.boxname]

    def setpath(self,path):
        self.path = path
        self.rootnode = LtrBoxRoot(self.path)

    def loadCookie(self,path):
        self.setpath(path)
        f = open(os.path.join(self.path,".ltr"),'r')
        self.fromUri(LtrContext(f.read().strip()))
        f.close()

    def writeCookie(self,path=False):
        if path:
            self.setpath(path)
        #FIXME: verify fileexists
        f = open(os.path.join(self.path,".ltr"),'w')
        f.write(self.uri)
        f.close()
        print "ltr: wrote cookie for ", self.name

    def setName(self,name=""):
        if name=="":
            if self.context.boxname:
                self.name = self.context.boxname
            else:
                self.name = uuid.uuid4().hex
        else:
            self.name = name

        self.uri = self.space.getBoxUri(self.name)

    def crawl(self):
        dirqueue=[self.rootnode]
        disapeared = []
        news = []
    
        while len(dirqueue):
            d = dirqueue.pop(0)
            print "ltr: crawl ",d.diskpath
            
            results = list(self.space.records.view("ltrcrawler/by-path",key=d.volpath))
            filter_this_box = lambda x: self.record["_id"] in x["value"]["present"] 
            results = filter(filter_this_box,results)
            known_files = dict(map(lambda x: (x["value"]["name"],x['value']),results))
            updates = []
            for l in d.children():
                now = {}
                meta = {}
                knownfile = False
                updated = False
                now["present"]= [self.record["_id"]]
                now["path"]= l.path
                now["name"]= l.name
                now["doctype"] = "node"
                meta['ftype'] = l.ftype
                meta['size'] = l.size
                meta['mtime'] = l.mtime
            
                if l.name in known_files:
                    knownfile = known_files[l.name]
                    print "ltr: known ",l.volpath
                else:
                    now["_id"]= uuid.uuid4().hex
                    
                if meta["ftype"] == "file" \
                and (not knownfile \
                or knownfile["meta"]["mtime"] != meta["mtime"]):
                    meta["hash"] = l.gethash()
                    meta["mime"] = l.getmime()
            
                if knownfile:
                    for attr in l.features:
                        if attr in meta:
                            if not attr in knownfile["meta"] \
                            or knownfile["meta"][attr] != meta[attr]:
                                updated=True
                                break
    
                now["meta"] = meta
            
                if not l.name in known_files:
                    print "ltr: new ", l.volpath
                    news.append(now)
                elif updated:
                    print "ltr: changed ", l.volpath
                    if not self.record["_id"] in knownfile["present"]:
                        knownfile["present"].append(self.record["_id"])
                    knownfile["meta"] = meta
                    updates.append(now)
            
                if l.ftype=="dir":
                    dirqueue.append(l)
            
                if l.name in known_files:
                    del known_files[l.name]
    
            #fixme: recurse into directories to delete 
            if len(known_files.keys()):
                for doc in known_files.itervalues():
                    print "ltr: disapeared ", doc["name"]
                    disapeared.append(doc)
            
            if len(updates):
                self.space.records.update(updates)
    
        for i,new in enumerate(news):
            def dictcompare (a,b,ks):
                for k in ks:
                    if not (k in a and k in b):
                        return False
                    if a[k] != b[k]:
                        return False
                return True
                
            trail = filter(lambda d: "hash" in new["meta"] \
                                    and hash in d["meta"] \
                                    and new["meta"]==d["meta"], disapeared)
            if len(trail): 
                old = trail[0]
                disapeared.remove(old)
                if len(old["present"] >1):
                    print "ltr: localmove ", new["name"]
                    continue
                else:
                    print "ltr: reappear ", new["name"]
                    news[i]["_id"] = old["_id"]
                    news[i]["_rev"] = old["_rev"]
    
        if len(news):
            self.space.records.update(news)
    
        updates = []
        for doc in disapeared:
            doc["_deleted"] =True
            updates.append(doc)
        self.space.records.update(updates)
        print "ltr: compact database"
        self.space.records.compact()
     
