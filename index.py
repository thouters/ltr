import os, shutil,sys
import uuid
# uuid.uuid4().hex
import pprint
import couchdb
from datetime import datetime

hostname = "maytag"
s = couchdb.Server('http://localhost:5984/')
try:
    del s['ltr']
except:
    pass

db = s.create('ltr')
db.update([couchdb.Document(_id='_design/index', language='javascript', views={
    'boxes': {
        'map': 'function(doc) { if (doc.doctype == "box") emit(doc._id,doc) }'
        },
    'nodes': {
        'map': 'function(doc) { if (doc.doctype == "node") emit(doc.path, doc._id) }'
        },
    'dirindex': {
        'map': 'function(doc) { if (doc.doctype == "node" && doc.ftype=="dir") emit(doc.path+"/"+doc.name, doc._id) }'
        },
})              ])

box1 = {"_id" : uuid.uuid4().hex, "doctype":"box", "synctime":datetime.now().ctime()}
box1["mount"] = {"maytag":"/home/thomas/Music"}
box2 = {"_id" : uuid.uuid4().hex, "doctype":"box", "synctime":datetime.now().ctime()}
box2["mount"] = {"maytag":"/home/thomas/box2"}
db.update([box1,box2])

def crawl(box,path=""):
    diskpath = os.path.join(box["mount"][hostname],path)
    names = os.listdir(diskpath)
    dirs = []
    entries = []
    for name in names:
        new = {}
        _id = uuid.uuid4().hex
        srcname = os.path.join(diskpath,name)
        if os.path.isfile(srcname):
            ftype = "file"
        elif os.path.isdir(srcname) and not os.path.ismount(srcname):
            ftype = "dir" 
        elif os.path.islink(srcname):
            ftype = "symlink"
            new["linkref"] = os.readlink(srcname)
        else:
            ftype="other"

        new["_id"]= _id

        bentry = {}
        if ftype != "symlink":
            s = os.stat(srcname)
            bentry["mtime"] = s.st_mtime
            bentry["hash"] = 'xxxx'
            bentry["size"] = s.st_size
        new["doctype"] = "node"
        new["path"]= "/"+path
        new["name"]= name
        new["ftype"]= ftype
        new["copies"] = {box1["_id"]:bentry}

        entries.append(new)

        if ftype=="dir":
            dirs.append(os.path.join(path,name))

    try:
        db.update(entries)
    except:
        pprint.pprint(entries)

    for d in dirs:
        crawl(box,d)

if __name__ == "__main__":
    crawl(box1)
    db.compact()
