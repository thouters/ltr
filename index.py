#!/usr/bin/env python

import os, shutil,sys
import uuid
import pprint
import couchdb
from datetime import datetime
from os.path import isfile, isdir, islink, ismount, join
from os import listdir, readlink, stat
import hashlib
import subprocess
from sys import argv
from socket import gethostname

views = {
    'boxes': { 'map': open("views/boxes/map.js").read() },
    'hashes': { 'map': open("views/hashes/map.js").read() },
    'nodes': { 'map': open("views/nodes/map.js").read() },
    'dirs': { 'map':  open("views/dirs/map.js").read() },
}

def crawl(db,workdir,box,path="/"):
    dirqueue=["/"]
    disapeared = []

    while len(dirqueue):
        path = dirqueue.pop(0)

        diskpath = workdir+path
        names = listdir(diskpath)
        
        if ".ltr" in names:
            if path != "/":
                print "ltr: skipping ltrdir ", diskpath
                continue
            names.remove(".ltr")
        
        if ".ltrignore" in names:
            f = open(diskpath+"/.ltrignore","r")
            ignores = f.readlines()
            f.close()
            if "." in ignores:
                continue
            for ignore in ignores:
                if ignore in names:
                    names.remove(ignore)
        
        print "ltr: crawl ",diskpath
        
        results = list(db.view("ltrcrawler/nodes",key=path))
        filter_this_box = lambda x: x["value"]["box"] == box["_id"]
        results = filter(filter_this_box,results)
        known_files = dict(map(lambda x: (x["value"]["name"],x['value']),results))
        #filter on box
        dirs = []
        news = []
        updates = []
        for filename in names:
            now = {}
            knownfile = False
            updated = False
            srcname = diskpath+"/"+filename
        
            if path == "/":
                volumepath = path+filename
            else:
                volumepath = path+"/"+filename

            now["box"]= box["_id"]
            now["path"]= path
            now["name"]= filename
            now["doctype"] = "node"
        
            if isfile(srcname):
                now['ftype'] = "file"
            elif isdir(srcname) and not ismount(srcname):
                now['ftype'] = "dir" 
            elif islink(srcname):
                now['ftype'] = "symlink"
                now["linkref"] = readlink(srcname)
            else:
                now['ftype'] = "other"
        
        
            if now['ftype'] != "symlink":
                st = stat(srcname)
                now["mtime"] = st.st_mtime
                now["size"] = st.st_size
        
            if filename in known_files:
                knownfile = known_files[filename]
                print "ltr: known ",volumepath
            else:
                now["_id"]= uuid.uuid4().hex
                
            if now["ftype"] == "file" \
            and (not knownfile \
            or knownfile["mtime"] != now["mtime"]):
                f = open(srcname)
                h = hashlib.sha1()
                print "ltr: digest ", volumepath
                h.update(f.read())
                now["hash"] = h.hexdigest()
                f.close()
                #fixme; no memory mapping possible
                magiccmd = "/usr/bin/file -b --mime-type -- -"
                fd = open(srcname,'r')
                now["mime"] = subprocess.Popen(magiccmd, shell=True, \
                     stdin=fd, stdout=subprocess.PIPE).communicate()[0]
                fd.close()
        
            if knownfile:
                for attr in ["ftype","mtime","size","hash"]:
                    if attr in now:
                        if not attr in knownfile or knownfile[attr] != now[attr]:
                            updated=True
                            break
        
            if not filename in known_files:
                print "ltr: new ", volumepath
                news.append(now)
            elif updated:
                print "ltr: changed ", volumepath
                now["_id"] = knownfile["_id"]
                updates.append(now)
        
            if now['ftype']=="dir":
                dirqueue.append(volumepath)
        
            if filename in known_files:
                del known_files[filename]

        #fixme: recurse into directories to delete 
        if len(known_files.keys()):
            for doc in known_files.itervalues():
                print "ltr: disapeared ", doc["name"]
                disapeared.append((doc["_id"],doc["_rev"],doc["hash"]))
        
        if len(updates):
            db.update(updates)

    for i,new in enumerate(news):
        trail = filter(lambda (_id,_rev,_hash): _hash == new["hash"], disapeared)
        if len(trail): 
            disapeared.remove(trail[0])
            (_id,_rev,_hash) = trail[0]
            print "ltr: reappear ", new["name"]
            news[i]["_id"] = _id
            news[i]["_rev"] = _rev

    if len(news):
        db.update(news)

    updates = []
    for (_id,_rev,_hash) in disapeared:
        doc = {"_id":_id, "_rev":_rev, "_deleted": True} 
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
        f = open(join(workdir,".ltr"),'r')
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
        f = open(join(workdir,".ltr"),'w')
        f.write(boxpath.strip("/")+"/"+boxid)
        f.close()
        print "Created database ", dbname
    else:
        db = server[dbname]
        box = db[boxid]

    crawl(db,workdir,box)

    box["synctime"] = datetime.now().ctime()
    db.update([box])
    db.compact()
    print "ltr: done"
