import os
from os.path import isfile
import uuid
from drop import LtrDrop
from space import LtrSpace
from uri import LtrUri

class LtrCookieException(Exception):
    pass

class LtrBox(LtrUri):

    def __repr__(self):
        s = "<ltrbox %s/%s >" % (self.space.name,self.name)
        return s

    def __init__(self,space=False):
        self.record = False
        self.name = False
        self.dropbox = False
        self.space = False
        self.uri=False
        self.path = False
        self.policy = "complete" # "skeleton" "ondemand" 
        self.cwd = False #set drop in loadcookie()

        if space:
            self.setSpace(space)

    def setSpace(self,space):
        self.space = space

    def setUri(self,uri):
        LtrUri.setUri(self,uri)
        self.name = self.boxname
        if not self.space:
            self.setSpace(LtrSpace().setUri(uri))

        self.getRecord()
        return self

    def getUri(self):
        return "/".join(self.dbserveruri.strip("/"),self.spacename)

    def createfromUri(self,uri):
        if not self.space:
            s = LtrSpace().createfromUri(uri)
            self.setSpace(s)
        LtrUri.setUri(self,uri)
        self.name = self.boxname
        self.create()
        return self

    def create(self):
        self.record = {}
        self.record["_id"] = self.name
        self.record["doctype"] = "box"
        self.record["policy"] = self.policy
        self.record["rootnode"] = "ROOT"
        print "ltr: new box to database ", self
        self.space.records.update([self.record])

    def getRecord(self):
        self.record = self.space.records[self.boxname]

    def setPath(self,path):
        self.path = path
        self.dropbox = LtrDrop().fromDisk(path)

    def fromCookie(self,path):
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
        self.setUri(c)
        self.setPath(testpath)
        f.close()
        return self

    def writeCookie(self,path=False):
        if path:
            self.setPath(path)
        #FIXME: verify fileexists
        f = open(os.path.join(self.path,".ltr"),'w')
        f.write(self.boxuri)
        f.close()
        print "ltr: wrote cookie for ", self.name

    def setName(self,name=""):
        if name=="":
            if self.boxname:
                self.name = self.boxname
            else:
                self.name = uuid.uuid4().hex
        else:
            self.name = name

        self.boxuri = self.space.getBoxUri(self.name)

    def pull(self,srcbox):
        print "ltr: pull ", srcbox.path

    def lsIndex(self):
        pass

    def crawl(self,commit=True):
        dirqueue=[self.dropbox]
        minus = []
        plus = []
        updates = []

        while len(dirqueue):
            parent = dirqueue.pop(0)
            #print "ltr: crawl ",parent.diskpath
            
            global_files = list(self.space.records.view("ltrcrawler/by-parent",key=parent.record["_id"]))
            filter_this_box = lambda x: self.record["_id"] in x["value"]["present"] 
            local_files = filter(filter_this_box,global_files)
            def mkdrop(doc):
                doc = doc["value"]
                return (doc["name"],LtrDrop().fromDoc(parent,doc))

            local_files = dict(map(mkdrop,local_files))
            for drop in parent.children():
                file_is_known = False
                file_changed = False
                drop.record["parent"]= parent.record["_id"]
                drop.record["present"]= [self.record["_id"]]
                drop.record["name"]= drop.name
                drop.record["doctype"] = "node"
                drop.record["meta"] = {}
                drop.record["meta"]['ftype'] = drop.ftype
                drop.record["meta"]['size'] = drop.size
                drop.record["meta"]['mtime'] = drop.mtime
                if drop.ftype == "dir":
                    drop.record["meta"]["path"]= drop.volpath
            
                if drop.name in local_files:
                    file_is_known = local_files[drop.name]
                    #print "ltr: known ",drop.volpath
                else:
                    drop.record["_id"]= uuid.uuid4().hex

                if drop.record["meta"]["ftype"] == "file" \
                and (not file_is_known \
                or file_is_known.record["meta"]["mtime"] != drop.record["meta"]["mtime"]):
                    if commit:
                        drop.record["meta"]["hash"] = drop.gethash()
                        drop.record["meta"]["mime"] = drop.getmime()
            
                if file_is_known:
                    for attr in drop.features:
                        if attr in drop.record["meta"]:
                            if not attr in file_is_known.record["meta"] \
                            or file_is_known.record["meta"][attr] != drop.record["meta"][attr]:
                                file_changed=True
                                break
    
            
                if not drop.name in local_files:
                    print "N", drop.volpath
                    plus.append(drop)
                elif file_changed:
                    print "M", drop.volpath
                    if not self.record["_id"] in file_is_known.record["present"]:
                        file_is_known.record["present"].append(self.record["_id"])
                    file_is_known.record["meta"] = drop.record["meta"]
                    updates.append(drop)
                else:
                    drop.record = file_is_known.record
            
                if drop.ftype=="dir":
                    dirqueue.append(drop)
            
                if drop.name in local_files:
                    del local_files[drop.name]
    
            #fixme: recurse into directories to delete 
            if len(local_files.keys()):
                for drop in local_files.itervalues():
                    minus.append(drop)
            
    
        for i,newdrop in enumerate(plus):
            #find new old files in list of removed files
            trail = filter(lambda d: "hash" in newdrop.record["meta"] \
                                    and hash in d["meta"] \
                                    and newdrop.record["meta"]==d["meta"], minus)
            if len(trail): 
                old = trail[0]
                minus.remove(old)
                if len(old["present"] >1):
                    print "R %s -> %s" %(old["name"],newdrop.record["name"])
                    continue
                else:
                    print "R %s -> %s" %(old["name"],newdrop.record["name"])
                    plus[i].record["_id"] = old["_id"]
                    plus[i].record["_rev"] = old["_rev"]
    
        updates += plus
    
        for doc in minus:
            doc["_deleted"] =True
            updates.append(doc)

        if commit:
            print "." * len(updates)
            updates = map(lambda x: x.record,updates)
            self.space.records.update(updates)
            #print "ltr: compact database"
            self.space.records.compact()

        if len(updates):
            return True
        else:
            return False
     
