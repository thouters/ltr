#!/usr/bin/env python
from sys import argv,path
from ltr import LtrBox,LtrContext
import os

if __name__ == "__main__":
    
    opts = argv
    opts.pop(0)
    if len(argv):
        cmd = opts.pop(0)
    else:
        cmd = "status"

    if cmd == "create":
        uri = opts.pop(0).strip()
        directory = opts.pop(0)
        box = LtrBox()
        box.setpath(directory)
        box.newFromUri(LtrContext(uri))
        box.writeCookie()
        box.crawl()

    if cmd == "clone":
        name = opts.pop(0).strip()
        src = opts.pop(0).strip()
        dst = opts.pop(0).strip()

        srcbox = LtrBox()
        srcbox.loadCookie(src)
        
        dstbox = LtrBox(srcbox.space)
        dstbox.setpath(dst)
        dstbox.setName(name)
        dstbox.writeCookie()

    if cmd == "status":
        if len(opts):
            directory = opts.pop(0)
        else:
            directory = os.getcwd()
        box = LtrBox()
        box.loadCookie(directory)
        box.crawl()

    print "ltr: done"
