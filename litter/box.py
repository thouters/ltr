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
        dirpath = fullvolpath[0:-len(fname)] # trailing /
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

    def pull(self,srcbox,dryrun=True):
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

            input_ = dictbyname(filter(sourcefilter,source.children()))
            updateable = dictbyname(filter(targetfilter,target.children()))

            absentfiles = set(input_.keys()) - set(updateable.keys())
            existingfiles = set(updateable.keys()) & set(input_.keys())

            for filename in existingfiles:
                #fixme, check deleted flag
                current = input_[filename]
                updating = updateable[filename]
                diff  = updating.diff(current)
                if diff != []:
                    show("M %s %s\n" %(current.volpath,diff))
                    wanted.append((current,updating))
                if updating.ftype == "dir":
                    queue.append((current,updating))

            for filename in absentfiles:
                current = input_[filename]
                absent = LtrNode().new()

                absent.name = current.name
                absent.path = current.path
                absent.boxname = self.id
                absent.deleted = True
                absent.addtime = time
                absent.isbox = False
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
        
            updating.deleted = False
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

            input_ = dictbyname(filter(sourcefilter,source.children()))
            updateable = dictbyname(filter(targetfilter,target.children()))

            newfiles = set(input_.keys()) - set(updateable.keys())
            absentfiles = set(updateable.keys()) - set(input_.keys())
            existingfiles = set(updateable.keys()) & set(input_.keys())

            for filename in existingfiles:
                existing = input_[filename]
                updating = updateable[filename]
                diff  = updating.diff(existing)
                if diff != []:
                    show("M %s %s\n" %(existing.volpath,diff))
                    show("[ updateDrop %s ]" % existing.name )
                    updating.updateDrop(existing)
                    updates.append(updating)
                if updating.ftype == "dir":
                    queue.append((existing,updating))

            for gone in map(lambda x:updateable.get(x),absentfiles):
                if gone.ftype == "dir":
                    queue.append((LtrDrop(gone.name,gone.path,self.fspath),gone))
                if gone.deleted != True:
                    show("D %s\n" %(gone.getVolPath()))
                gone.deleted = True
                updates.append(gone)
                if self.policy == "complete":
                    show("w %s\n" %(gone.getVolPath()))

            for new in map(lambda x:input_.get(x),newfiles):

                newnode = LtrNode().new()

                show("[ updateDrop %s ]" % new.volpath )
                newnode.updateDrop(new,dryrun=dryrun)
                newnode.boxname = self.id
                newnode.deleted = False
                newnode.addtime = time
                newnode.isbox = False
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
        self.isbox = True
        self.doctype = "node"
        self.policy = "complete"
        print "ltr: new box to database ", self
        self.store(self.space.records)

    @classmethod
    def createfromUri(self,uri):
        LtrUri.setUri(self,uri)
        self.name = self.boxname
        self.create()
        return self


