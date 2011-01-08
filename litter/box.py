import os
from drop import LtrDrop
from uri import LtrUri
from node import LtrNode
from couchdb.mapping import TextField
import shutil
import sys
import uuid


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
        return os.path.join(self.cwd,relativetocwd)

    def getDrop(self,fullvolpath):
        fname = fullvolpath.split("/")[-1]
        dirpath = fullvolpath[0:-len(fname)] # trailing /
        if dirpath!="/":
            qpath=dirpath.rstrip("/")
        nodes = list(LtrNode.view(self.space.records,"ltrcrawler/path",key=[qpath,fname],include_docs=True))
        nodes = filter(lambda x: x.boxname == self.id,nodes)
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

    def pull(self,srcbox,startNode=False,dryrun=True):
        print "ltr: pull ", srcbox.path
        treeQueue=[]
        updates = []
        if startNode == False:
            startNode = self

        #print startNode
        treeQueue.append(startNode)

        while len(treeQueue):
            node= treeQueue.pop(0)
            nodes = node.children()
            #nodes = dict(map(lambda node: (node.name,node),nodes))
        
            if self.policy == "complete":
                wanted = filter(lambda n: \
                    self.id not in n.present and srcbox.id in n.present \
                    ,nodes)
            elif self.policy == "ondemand":
                wanted = filter(lambda n: \
                    self.id not in n.present and srcbox.id in n.wanted \
                    ,nodes)

            for node in wanted:
                src = os.path.join(srcbox.fspath,node.path.strip("/"),node.name)
                dst = os.path.join(self.fspath,node.path.strip("/"),node.name)
                if node.ftype != "dir":
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
                    treeQueue.append(node)

                node.present.append(self.id)
                updates.append(node)

        if not dryrun:
            print "." * len(updates)
            self.space.records.update(updates)

        if len(updates):
            #import pprint
            #pprint.pprint(updates)
            return True
        else:
            return False


    def commit(self,startNode=False,dryrun=True):
        def show(x):
            sys.stdout.write("\r"+ x.replace("\n"," "*20+"\n"))
            sys.stdout.flush()
        treeQueue=[]
        updates = []
        if startNode == False:
            startNode = self

        #print startNode
        treeQueue.append( (LtrDrop("","/",self.fspath),startNode) )

        while len(treeQueue):
            (drop,node)= treeQueue.pop(0)
            nodes = node.children()
            drops = drop.children()
            nodes = dict(map(lambda node: (node.name,node),nodes))
            drops = dict(map(lambda drop: (drop.name,drop),drops))

            newkeys = set(drops.keys()) - set(nodes.keys())
            lesskeys = set(nodes.keys()) - set(drops.keys())
            staykeys = set(nodes.keys()) & set(drops.keys())

            for filename in staykeys:
                localnode = nodes[filename]
                localdrop = drops[filename]
                diff  = localnode.diff(localdrop)
                if diff != []:
                    show("M %s %s\n" %(localdrop.volpath,diff))
                    show("[ updateDrop %s ]" % localdrop.name )
                    localnode.boxname = self.id
                    localnode.updateDrop(localdrop)
                    updates.append(localnode)
                if localnode.ftype == "dir":
                    treeQueue.append((localdrop,localnode))

            for nonlocalnode in map(lambda x:nodes.get(x),lesskeys):
                if nonlocalnode.ftype == "dir":
                    treeQueue.append((LtrDrop(nonlocalnode.name,nonlocalnode.path,self.fspath),nonlocalnode))
                if self.id in nonlocalnode.present:
                    nonlocalnode.present.remove(self.id)
                    show("D %s\n" %(nonlocalnode.getVolPath()))
                    updates.append(nonlocalnode)
                else:
                    if self.policy == "complete":
                        show("w %s\n" %(nonlocalnode.getVolPath()))

            for newdrop in map(lambda x:drops.get(x),newkeys):

                newnode = LtrNode().new()

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
        self.id = self.boxname
        self.path = "/"
        self.name = ""
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


