import os
from os.path import isfile
from drop import LtrDrop
from uri import LtrUri
from node import LtrNode
from couchdb.mapping import *
import sys

class LtrCookieException(Exception):
    pass

class LtrBox(LtrUri,Document):
    doctype = TextField()
    policy = TextField()
    rootnode = TextField()

    def __repr__(self):
        s = "<ltrbox %s/%s >" % (self.space.name,self.name)
        return s

    def __init__(self,space=False):
        Document.__init__(self)
        self.record = False
        self.name = False
        self.dropbox = False
        self.space = False
        self.uri=False
        self.path = False
        self.cwd = False #set drop in loadcookie()

        if space:
            self.setSpace(space)

    def setSpace(self,space):
        self.space = space
        return self

    def setUri(self,uri):
        LtrUri.setUri(self,uri)
        self.name = self.boxname

        return self

    def getUri(self):
        return "/".join(self.dbserveruri.strip("/"),self.spacename)

    def getDrop(self,fullvolpath):
        fname = fullvolpath.split("/")[-1]
        dirpath = fullvolpath[0:-len(fname)]
        #query view to get parent
        if dirpath=="/":
            qpath="ROOT"
        else:
            qpath=dirpath
        parent= list(LtrNode.view(self.space.records,"ltrcrawler/tree",key=qpath))
        if 0==len(parent):
            child=None
        else:
            parent = parent[0]
            child= list(LtrNode.view(self.space.records,"ltrcrawler/by-parent",key=[parent._id,fname]))
            child.setParent(parent)
        return child

    def getRootNode(self):
        return LtrNode.load(self.space.records,self.rootnode).connect(self.space,False)

    def setPath(self,path):
        self.path = path
        self.dropbox = LtrDrop().fromDisk(path)

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

    def pull(self,srcbox,startNode=False,dryrun=True):
        print "ltr: pull ", srcbox.path
        for src in []:
            print "cp %s %s " % (src,dst)
            if not dryrun:
                try:
                    shutil.copy2(src,dst)
                    drop.record["present"].append(self.name)
                    updates.append(drop)
                except:
                    print "error"
        return False

    def commit(self,startNode=False,dryrun=True):
        def show(x):
            sys.stdout.write("\r"+ x.replace("\n"," "*20+"\n"))
            sys.stdout.flush()
        treeQueue=[]
        updates = []
        if startNode == False:
            startNode = self.getRootNode()

        #print startNode
        treeQueue.append( (self.dropbox,startNode) )

        while len(treeQueue):
            (drop,node)= treeQueue.pop(0)
            nodes = node.children()
            drops = drop.children()
            nodes = dict(map(lambda node: (node.name,node),nodes))
            drops = dict(map(lambda drop: (drop.name,drop),drops))

            #allkeys = set(drops.keys()) | set(nodes.keys())
            newkeys = set(drops.keys()) - set(nodes.keys())
            lesskeys = set(nodes.keys()) - set(drops.keys())
            staykeys = set(nodes.keys()) & set(drops.keys())

            for filename in staykeys:
                localnode = nodes[filename]
                localdrop = drops[filename]
                diff  = localnode.diff(localdrop)
                if diff != []:
                    show("M %s %s\n" %(localdrop.volpath,diff))
                    show("[ updateDrop %s ]" % localdrop.volpath )
                    localnode.updateDrop(localdrop)
                    updates.append(localnode)
                if localnode.meta.ftype == "dir":
                    treeQueue.append((localdrop,localnode))

            for nonlocalnode in map(lambda x:nodes.get(x),lesskeys):
                if nonlocalnode.meta.ftype == "dir":
                    treeQueue.append((LtrDrop(),nonlocalnode))
                if self.id in nonlocalnode.present:
                    nonlocalnode.present.remove(self.id)
                    show("D %s\n" %(nonlocalnode.getVolPath()))
                    updates.append(nonlocalnode)

            for newdrop in map(lambda x:drops.get(x),newkeys):

                newnode = LtrNode().new(node.id)

                if not self.id in newnode.present:
                    show("[ updateDrop %s ]" % newdrop.volpath )
                    newnode.updateDrop(newdrop,dryrun=dryrun)
                    newnode.present.append(self.id)
                    show("N %s\n" %(newdrop.volpath))
                    updates.append(newnode)

                if newdrop.ftype == "dir":
                    treeQueue.append((newdrop,newnode))

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
        self.id = self.name
        self.doctype = "box"
        self.policy = "complete"
        self.rootnode = "ROOT"
        print "ltr: new box to database ", self
        self.store(self.space.records)

    @classmethod
    def createfromUri(self,uri):
        LtrUri.setUri(self,uri)
        self.name = self.boxname
        self.create()
        return self


