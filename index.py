#!/usr/bin/env python

import uuid
import couchdb
from datetime import datetime
from sys import argv
from ltr import LtrBoxRoot
import os.path

views = {
    'boxes': { 'map': open("views/boxes/map.js").read() },
    'hashes': { 'map': open("views/hashes/map.js").read() },
    'by-path': { 'map': open("views/by-path/map.js").read() },
    'dirs': { 'map':  open("views/dirs/map.js").read() },
}


   

def crawl(db,ltrboxroot,box):
    dirqueue=[ltrboxroot]
    disapeared = []
    news = []

    while len(dirqueue):
        d = dirqueue.pop(0)
        print "ltr: crawl ",d.diskpath
        
        results = list(db.view("ltrcrawler/by-path",key=d.volpath))
        filter_this_box = lambda x: box["_id"] in x["value"]["present"] 
        results = filter(filter_this_box,results)
        known_files = dict(map(lambda x: (x["value"]["name"],x['value']),results))
        updates = []
        for l in d.children():
            now = {}
            meta = {}
            knownfile = False
            updated = False
            now["present"]= [box["_id"]]
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
                if not box["_id"] in knownfile["present"]:
                    knownfile["present"].append(box["_id"])
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
            db.update(updates)

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
        db.update(news)

    updates = []
    for doc in disapeared:
        doc["_deleted"] =True
        updates.append(doc)
    db.update(updates)
        

if __name__ == "__main__":

    if argv[1] == "--init":
        boxpath = argv[2]
        (http,slashslash,serveruri,dbname) = boxpath.split("/",3)
        workdir = argv[3].strip()
        boxid = uuid.uuid4().hex
    else:
        workdir = argv[1]
        f = open(os.path.join(workdir,".ltr"),'r')
        ref = f.read().strip()
        f.close()
        (http,slashslash,serveruri,dbname,boxid) = ref.split('/',4)
        print "ltr: connect ", serveruri, dbname, boxid

    server = couchdb.Server("http://"+serveruri)
        
    if argv[1] == "--init":
        if dbname in server:
            del server[dbname]
        db = server.create(dbname)
        db.update([couchdb.Document(_id='_design/ltrcrawler', language='javascript', views=views)])
        box = {"_id" : boxid, "doctype":"box","usually-at":workdir, "policy":"?"}
        db.update([box])
        f = open(os.path.join(workdir,".ltr"),'w')
        f.write(boxpath.strip("/")+"/"+boxid)
        f.close()
        print "Created database ", dbname
    else:
        db = server[dbname]
        box = db[boxid]

    crawl(db,LtrBoxRoot(workdir),box)

    box["synctime"] = datetime.now().ctime()
    db.update([box])
    db.compact()
    print "ltr: done"
