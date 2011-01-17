import os
from drop import LtrDrop
from uri import LtrUri
from node import LtrNode
from couchdb.mapping import TextField
import shutil
import sys
import uuid

from pprint import pprint
def show(x):
    sys.stdout.write("\r"+ x.replace("\n"," "*20+"\n"))
    sys.stdout.flush()

def dictbyname(l):
    return dict(map(lambda x: (x.name,x),l))


class LtrBox(LtrUri,LtrNode):
    policy = TextField()
    rootnode = TextField()
    boxurl = TextField()
    couchurl = TextField()

    def info(self):
        s = ""
        s += "policy: %s\n" % self.policy
        s += "boxurl: %s\n" % self.boxurl
        s += "couchurl: %s\n" % self.couchurl
        return s

    def __repr__(self):
        s = "<ltrbox %s/%s >" % (self.space.name,self.id)
        return s

    def __init__(self,space=False):
        LtrNode.__init__(self)
        LtrUri.__init__(self)
        self.record = False
        self.name = False
        self.space = False
        self.uri=False
        self.cwd = False #set drop in loadcookie()

        if space:
            self.setSpace(space)

    def setSpace(self,space):
        self.space = space
        return self

    def setUri(self,uri):
        LtrUri.setUri(self,uri)

        return self

    def getUri(self):
        return "/".join(self.dbserveruri.strip("/"),self.spacename)

    def pathConv(self,relativetocwd):
        s = os.path.join(self.cwd,relativetocwd)
        return s.rstrip("/")

    def getNode(self,fullvolpath):
        fname = fullvolpath.split("/")[-1]
        dirpath = fullvolpath[0:-len(fname)].rstrip("/") # trailing /
        if dirpath=="":
            dirpath = "/"
        nodes = list(LtrNode.view(self.space.records,"ltrcrawler/path",key=[dirpath,fname],include_docs=True))
        nodes = filter(lambda x: x.boxname == self.id ,nodes)
        if 0==len(nodes):
            return None
        node = nodes[0]
        node.connect(self.space)
        return node

    def getRootNode(self):
        return LtrNode.load(self.space.records,self.rootnode).connect(self.space,False)

    def setPath(self,path):
        self.path = path

    def writeCookie(self,path=False):
        if path:
            self.fspath = path
        #FIXME: verify fileexists
        f = open(os.path.join(self.fspath,".ltr"),'w')
        f.write(self.boxuri)
        f.close()
        print "ltr: wrote cookie for ", self.boxname

    def setName(self,name=""):
        self.boxname = name
        self.boxuri = self.space.getBoxUri(self.boxname)

    def fetch(self,srcbox,dryrun=True):
        print "ltr: pull ", srcbox.fspath
        queue=[]
        updates = []
        wanted = []

        import datetime
        time = datetime.datetime.now()
        queue.append((srcbox,self))

        targetfilter = lambda n: n.boxname == self.id 
        sourcefilter = lambda n: n.boxname == srcbox.id

        while len(queue):
            (source,target)= queue.pop(0)

            source = dictbyname(filter(sourcefilter,source.children()))
            target = dictbyname(filter(targetfilter,target.children()))

            srcunique = set(source.keys()) - set(target.keys())
            common = set(target.keys()) & set(source.keys())

            for filename in common:
                #fixme, query DB for matching size,hash tuples
                current = source[filename]
                updating = target[filename]
                if "skip" in updating.flags:
                    continue
                if not "copy" in current.flags:
                    continue
                diff  = updating.diff(current)
                if diff != []:
                    show("M %s %s\n" %(current.getVolPath(),diff))
                    wanted.append((current,updating))
                if updating.ftype == "dir":
                    queue.append((current,updating))

            # nodes absent but wanted
            for filename in srcunique:
                current = source[filename]
                absent = LtrNode().new()

                absent.name = current.name
                absent.path = current.path
                absent.boxname = self.id
                if "copy" in absent.flags:
                    absent.flags.append("copy")
                absent.addtime = time
                show("w %s\n" %(absent.getVolPath()))
                if current.ftype == "dir":
                    queue.append((current,absent))
                wanted.append((current,absent))

        for (current,updating) in wanted:
            src = os.path.join(srcbox.fspath,current.getVolPath().strip("/"))
            dst = os.path.join(self.fspath,updating.getVolPath().strip("/"))
            if current.ftype != "dir":
                print "cp %s %s " % (src,dst)
                if not dryrun:
                    shutil.copy2(src,dst)
                    try:
                        shutil.copy2(src,dst)
                    except:
                        print "error"
            else:
                print "mkdir %s " % dst
                if not dryrun:
                    os.mkdir(dst)
        
            if not "copy" in updating.flags:
                updating.flags.append("copy")
            if "deleted" in updating.flags:
                updating.flags.remove("deleted")
            updating.log.append({"dt": time, "etype": "pull", "old":current.id})
            updating.updateDrop(current)
            updates.append(updating)

        if not dryrun:
            print "." * len(updates)
            self.space.records.update(updates)

        if len(updates):
            #import pprint
            #pprint.pprint(updates)
            return True
        else:
            return False


    def commit(self,dryrun=True):
        """ update target with data from source """
        queue=[]
        updates = []

        import datetime
        time = datetime.datetime.now()

        queue.append( (LtrDrop("","/",self.fspath),self) )

        sourcefilter = lambda n: True
        targetfilter = lambda n: n.boxname == self.id 

        while len(queue):
            (source,target)= queue.pop(0)

            source = dictbyname(filter(sourcefilter,source.children()))
            target = dictbyname(filter(targetfilter,target.children()))

            srcunique = set(source.keys()) - set(target.keys())
            absent = set(target.keys()) - set(source.keys())
            common = set(target.keys()) & set(source.keys())

            for filename in common:
                existing = source[filename]
                updating = target[filename]
                diff  = updating.diff(existing)
                if diff != []:
                    show("M %s %s\n" %(existing.volpath,diff))
                    show("[ updateDrop %s ]" % existing.name )
                    updating.updateDrop(existing)
                    updates.append(updating)
                if updating.ftype == "dir":
                    queue.append((existing,updating))

            for gone in map(lambda x:target.get(x),absent):
                if gone.ftype == "dir":
                    queue.append((LtrDrop(gone.name,gone.path,self.fspath),gone))
                if "copy" in absent.flags:
                    show("D %s\n" %(gone.getVolPath()))
                if "copy" in absent.flags:
                    absent.flags.remove("copy")
                updates.append(gone)
                if self.policy == "complete":
                    show("w %s\n" %(gone.getVolPath()))

            for new in map(lambda x:source.get(x),srcunique):

                newnode = LtrNode().new()

                show("[ updateDrop %s ]" % new.volpath )
                newnode.updateDrop(new,dryrun=dryrun)
                newnode.boxname = self.id
                if not "copy" in newnode.flags:
                    newnode.flags.append("copy")
                newnode.addtime = time
                show("N %s\n" %(new.volpath))
                updates.append(newnode)

                if new.ftype == "dir":
                    queue.append((new,newnode))

        if not dryrun:
            print "." * len(updates)
            self.space.records.update(updates)

        if len(updates):
            #import pprint
            #pprint.pprint(updates)
            return True
        else:
            return False

    def create(self):
        self.id = self.boxname
        self.path = "/"
        self.name = ""
        self.flags = ["copy","boxroot"]
        self.doctype = "node"
        self.policy = "complete"
        self.couchurl = self.spaceuri
        print "ltr: new box to database ", self
        self.store(self.space.records)

    @classmethod
    def createfromUri(cls,uri):
        s = cls()
        LtrUri.setUri(s,uri)
        s.name = s.boxname
        s.create()
        return s


