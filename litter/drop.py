from os.path import isfile, isdir, islink, ismount, join
import hashlib
import subprocess
from os import listdir, stat
import unittest
from uri import LtrUri


class LtrDrop(LtrUri):
    def __init__(self):
        self.record = {}
        self.ignoreFileName=".ltrignore"

    def fromDisk(self,name,parentdrop=False):
        """ """
        if parentdrop:
            self.parent = parentdrop
            self.volroot = self.parent.volroot
            self.name = name
            self.path = join(self.parent.path,self.parent.name)
            self.volpath = join(self.path,name)
            self.diskpath = join(self.volroot,self.volpath.strip("/"))
        else:
            self.diskpath = name
            self.volroot = name
            self.path="/"
            self.volpath="/"
            self.name=""
            #self.record["_id"] = "ROOT"
   
        if isfile(self.diskpath):
            self.ftype = "file"
            self.features = ["ftype","mtime","size"]
        elif isdir(self.diskpath):
            self.ftype = "dir" 
            self.features = ["ftype"]
        elif islink(self.diskpath):
            self.ftype = "symlink"
            self.features = ["ftype","mtime"]
        else:
            raise Exception, "filetype not handled!"

        st = stat(self.diskpath)
        self.mtime = int(st.st_mtime)
        self.size = st.st_size
        return self

    def fromDoc(self,parent,doc):
        self.parent = parent
        self.record = doc
        self.name = doc["name"]
        self.volpath = join(parent.volpath,self.name)
        return self


    def children(self):
        if self.ftype != "dir":
            return []
        if ismount(self.diskpath) and self.volpath !="":
            print "ltr: skip mount ", self.diskpath
            return []
        names = listdir(self.diskpath)
        if ".ltr" in names:
            if self.volpath != "/":
                print "ltr: skip ltrbox ", self.diskpath
            names.remove(".ltr")
        
        if self.ignoreFileName in names:
            f = open(join(self.diskpath,self.ignoreFileName),"r")
            ignores = f.readlines()
            f.close()
            #FIXME: use glob
            if "." in ignores:
                return []
            for ignore in ignores:
                if ignore in names:
                    names.remove(ignore)
        return map(lambda n: LtrDrop().fromDisk(n,self),names)


    def calcHash(self):
        """ calculate sha1sum of file contents self.diskpath """
        if isdir(self.diskpath):
            return ""
        if islink(self.diskpath):
            h = hashlib.sha1()
            h.update(os.readlink(self.diskpath))
            h = h.hexdigest()
        else:
            import subprocess
            p = subprocess.Popen("sha1sum \"%s\""%self.diskpath, shell=True, stdout=subprocess.PIPE)
            h, filename = p.communicate()[0].split(" ",1)
            #f = open(self.diskpath)
            #h.update(f.read())
            #f.close()
        return h

    def calcMime(self):
        """ Determine mimetype from diskpath """
        if isdir(self.diskpath):
            return "application/x-directory"
        if islink(self.diskpath):
            return "application/x-symlink"
        magiccmd = "/usr/bin/file -b --mime-type -- -"
        fd = open(self.diskpath,'r')
        m = subprocess.Popen(magiccmd, shell=True, \
             stdin=fd, stdout=subprocess.PIPE).communicate()[0]
        fd.close()
        return m.strip()



class LtrFileTest(unittest.TestCase):
    tinypng ="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAACklEQVR4nGMAAQAABQABDQottAAA\nAABJRU5ErkJggg==\n"
    tinypngsha1sum = "c530c06cf89c410c0355d7852644a73fc3ec8c04"
    tinypngsize = 67
    def setUp(self):
        import tempfile, base64, os.path, os
        self.tempdir = tempfile.mkdtemp()
        self.pngfile = "pngfile"
        self.ltrignorefile = LtrDrop().ignoreFileName
        self.ignoredfile = "PleaseIgnoreMe"

        f = open(os.path.join(self.tempdir,self.pngfile),"w")
        pngcontents = base64.decodestring(self.tinypng)
        f.write(pngcontents)
        f.close()

        f = open(os.path.join(self.tempdir,self.ltrignorefile),"w")
        f.write(self.ignoredfile)
        f.close()

        f = open(os.path.join(self.tempdir,self.ignoredfile),"w")
        f.write("ignore me!!!");
        f.close()
        
        self.childdir1 = "directory1"
        os.mkdir(os.path.join(self.tempdir,self.childdir1))
        self.nestedfile = "nested1"
        f = open(os.path.join(self.tempdir,self.childdir1,self.nestedfile),"w")
        f.write("xyz")
        f.close()

        self.dropbox = LtrDrop().fromDisk(self.tempdir)

    def testMime(self):
        a = LtrDrop().fromDisk(self.pngfile,self.dropbox) 
        self.assertEqual(a.calcMime(),"image/png")

    def testSize(self):
        a = LtrDrop().fromDisk(self.pngfile,self.dropbox) 
        self.assertEqual(a.size,self.tinypngsize)

    def testHash(self):
        rootfiles = self.dropbox.children()
        pngfile = filter(lambda x: x.name == self.pngfile,rootfiles)[0]
        self.assertEqual(pngfile.calcHash(),self.tinypngsha1sum)

    def testlocation(self):
        rootfiles = self.dropbox.children()
        pngfile = filter(lambda x: x.name == self.pngfile,rootfiles)[0]
        self.assertEqual(pngfile.path,"/")

    def testCrawling(self):
        dirqueue = [self.dropbox]
        found = []
        while len(dirqueue):
            d = dirqueue.pop(0)
            self.assertTrue(len(d.children())>0)
            for drop in d.children():
                found.append(drop)
                if len(drop.children()):
                    dirqueue.append(drop)

        filenames = map(lambda x: x.name,found)
        self.assertTrue(self.pngfile in filenames)
        self.assertTrue(self.nestedfile in filenames)
        self.assertTrue(self.childdir1 in filenames)

    def testIgnoreFile(self):
        matches = filter(lambda x: x.name == self.ignoredfile,self.dropbox.children())
        self.assertFalse(len(matches)>0)


if __name__=="__main__":
    unittest.main()
