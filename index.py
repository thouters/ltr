#!/usr/bin/env python
from sys import argv,path
from ltr import LtrBox,LtrUri

if __name__ == "__main__":
    
    if argv[1] in ["--create"]:
        box = LtrBox()
        box.setpath(argv[3].strip())
        box.newFromUri(LtrUri(argv[2]))
        box.uri.connectDatabaseServer()
        box.writeCookie()
    else:
        box = LtrBox()
        box.loadCookie(argv[1])
        box.uri.connectDatabaseServer()

    box.crawl()
    print "ltr: done"
