#!/usr/bin/env python

import os, shutil,sys
import uuid
import pprint
import couchdb
from datetime import datetime
from os.path import isfile, isdir, islink, ismount, join
from os import listdir, readlink, stat
import hashlib
from sys import argv
from socket import gethostname

views = {
    'boxes': { 'map': open("views/boxes/map.js").read() },
    'nodes': { 'map': open("views/nodes/map.js").read() },
    'dirs': { 'map':  open("views/dirs/map.js").read() },
}

def crawl(db,workdir,box,path="/"):
    diskpath = workdir+path
    names = listdir(diskpath)

    if ".ltr" in names:
        if path != "/":
            print "ltr: skipping ltrdir ", diskpath
            return
        names.remove(".ltr")

    print "ltr: scanning ",diskpath

    results = list(db.view("ltrcrawler/nodes",key=path))
    filter_this_box = lambda x: x["value"]["box"] == box["_id"]
    results = filter(filter_this_box,results)
    known_files = dict(map(lambda x: (x["value"]["name"],x['value']),results))
    #filter on box
    dirs = []
    entries = []
    for filename in names:
        now = {}
        knownfile = False
        updated = False
        srcname = diskpath+"/"+filename

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
        else:
            now["_id"]= uuid.uuid4().hex
            
        if now["ftype"] == "file" \
        and (not knownfile \
        or knownfile["mtime"] != now["mtime"]):
            f = open(srcname)
            h = hashlib.sha1()
            print "Digest ", srcname
            h.update(f.read())
            now["hash"] = h.hexdigest()
            f.close()

        if knownfile:
            for attr in ["ftype","mtime","size","hash"]:
                if attr in now:
                    if not attr in knownfile or knownfile[attr] != now[attr]:
                        updated=True
                        break

        if not filename in known_files:
            print "new file: ", srcname
            entries.append(now)
        elif updated:
            print "file changed: ", srcname
            print knownfile, now
            now["_id"] = knownfile["_id"]
            entries.append(now)

        if now['ftype']=="dir":
            if path == "/":
                dirs.append(path+filename)
            else:
                dirs.append(path+"/"+filename)

        if filename in known_files:
            del known_files[filename]

    #fixme: recurse into directories to delete 
    if len(known_files.keys()):
        for doc in known_files.itervalues():
            print "ltr: removed ", doc["name"]
            doc["_deleted"] = True
            entries.append(doc)

    if len(entries):
        db.update(entries)

    for directory in dirs:
        crawl(db,workdir,box,directory)

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
        f.write(boxpath.strip("/")+boxid)
        f.close()
        print "Created database ", dbname
    else:
        db = server[dbname]
        box = db[boxid]

    crawl(db,workdir,box)

    box["synctime"] = datetime.now().ctime()
    db.update([box])
    db.compact()
    print "ltr done."
