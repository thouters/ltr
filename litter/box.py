import os
from os.path import isfile
import uuid
from .drop import LtrBoxRoot
from .space import LtrSpace
from .context import LtrContext

class LtrCookieException(Exception):
    pass

class LtrBox:
    record = False
    name = False
    dropbox = False
    space = False
    context = False
    uri=False
    policy = "complete" # "skeleton" "ondemand" 

    def __repr__(self):
        s = "<ltrbox %s/%s >" % (self.space.name,self.name)
        return s

    def __init__(self,space=False):
        if space:
            self.setSpace(space)

    def setSpace(self,space):
        self.space = space
        self.space.boxes.append(self)

    def fromUri(self,context):
        if not self.context:
            self.context = context
        if not self.space:
            self.setSpace(LtrSpace())
            self.space.fromUri(context)

        self.name = context.boxname
        self.getRecord()

    def newFromUri(self,context):
        if not self.space:
            s = LtrSpace()
            self.context = context
            s.newFromUri(self.context)
            self.setSpace(s)
        self.name = context.boxname
        self.uri = context.boxuri
        self.new()

    def new(self):
        self.record = {}
        self.record["_id"] = self.name
        self.record["doctype"] = "box"
        self.record["policy"] = self.policy
        self.record["rootnode"] = "ROOT"
        print "ltr: new box to database ", self
        self.space.records.update([self.record])

    def getRecord(self):
        self.record = self.space.records[self.context.boxname]

    def setPath(self,path):
        self.path = path
        self.dropbox = LtrBoxRoot(self.path)

    def loadCookie(self,path):
        self.setPath(path)
        cookiefile = os.path.join(self.path,".ltr")
        if not isfile(cookiefile):
            raise LtrCookieException("directory is not a litter dropbox: %s"%self.path)
        f = open(cookiefile,'r')
        self.fromUri(LtrContext(f.read().strip()))
        f.close()

    def writeCookie(self,path=False):
        if path:
            self.setPath(path)
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

    def pull(self,srcbox):
        print "ltr: pull ", srcbox.path

        #self.record.rootnode._id
        dirqueue=[self.dropbox]
        minus = []
        plus = []
        while len(dirqueue):
            d = dirqueue.pop(0)
            print "ltr: crawl ",d.diskpath


    def crawl(self):
        dirqueue=[(self.dropbox,self.space.records[self.record["rootnode"]])]
        minus = []
        plus = []
    
        while len(dirqueue):
            (parent,parentdoc) = dirqueue.pop(0)
            print "ltr: crawl ",parent.diskpath
            
            global_files = list(self.space.records.view("ltrcrawler/by-parent",key=parentdoc["_id"]))
            filter_this_box = lambda x: self.record["_id"] in x["value"]["present"] 
            local_files = filter(filter_this_box,global_files)
            local_files = dict(map(lambda x: (x["value"]["name"],x['value']),local_files))
            updates = []
            for l in parent.children():
                now = {}
                meta = {}
                file_is_known = False
                file_changed = False
                now["parent"]= parentdoc["_id"]
                now["present"]= [self.record["_id"]]
                now["name"]= l.name
                now["doctype"] = "node"
                meta['ftype'] = l.ftype
                meta['size'] = l.size
                meta['mtime'] = l.mtime
                if l.ftype == "dir":
                    meta["path"]= l.volpath
            
                if l.name in local_files:
                    file_is_known = local_files[l.name]
                    print "ltr: known ",l.volpath
                else:
                    now["_id"]= uuid.uuid4().hex
                    
                if meta["ftype"] == "file" \
                and (not file_is_known \
                or file_is_known["meta"]["mtime"] != meta["mtime"]):
                    meta["hash"] = l.gethash()
                    meta["mime"] = l.getmime()
            
                if file_is_known:
                    for attr in l.features:
                        if attr in meta:
                            if not attr in file_is_known["meta"] \
                            or file_is_known["meta"][attr] != meta[attr]:
                                file_changed=True
                                break
    
                now["meta"] = meta
            
                if not l.name in local_files:
                    print "ltr: new ", l.volpath
                    plus.append(now)
                    doc = now
                elif file_changed:
                    print "ltr: changed ", l.volpath
                    if not self.record["_id"] in file_is_known["present"]:
                        file_is_known["present"].append(self.record["_id"])
                    file_is_known["meta"] = meta
                    updates.append(now)
                    doc=now
                else:
                    doc = file_is_known
            
                if l.ftype=="dir":
                    dirqueue.append((l,doc))
            
                if l.name in local_files:
                    del local_files[l.name]
    
            #fixme: recurse into directories to delete 
            if len(local_files.keys()):
                for doc in local_files.itervalues():
                    print "ltr: minus ", doc["name"]
                    minus.append(doc)
            
            if len(updates):
                self.space.records.update(updates)
    
        for i,new in enumerate(plus):
            def dictcompare (a,b,ks):
                for k in ks:
                    if not (k in a and k in b):
                        return False
                    if a[k] != b[k]:
                        return False
                return True
                
            trail = filter(lambda d: "hash" in new["meta"] \
                                    and hash in d["meta"] \
                                    and new["meta"]==d["meta"], minus)
            if len(trail): 
                old = trail[0]
                minus.remove(old)
                if len(old["present"] >1):
                    print "ltr: localmove ", new["name"]
                    continue
                else:
                    print "ltr: reappear ", new["name"]
                    plus[i]["_id"] = old["_id"]
                    plus[i]["_rev"] = old["_rev"]
    
        if len(plus):
            self.space.records.update(plus)
    
        updates = []
        for doc in minus:
            doc["_deleted"] =True
            updates.append(doc)
        self.space.records.update(updates)
        print "ltr: compact database"
        self.space.records.compact()
     
