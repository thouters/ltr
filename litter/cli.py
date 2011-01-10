#!/usr/bin/env python
from space import LtrSpace
from box import LtrBox
from uri import LtrUri
import os
import argparse
import sys
import couchdb.client

class LtrCli:
    def __init__(self,argv):
        if argv==[]:
            argv=["status"]
        parser = argparse.ArgumentParser(\
            description="ltr - Decentralised personal file distribution",\
            prog='ltr')
        parser.add_argument('-n','--dryrun',help='dryrun',action="store_true")

        subparsers = parser.add_subparsers(title="commands")

        init_ = subparsers.add_parser('init',help="create new database")
        init_.add_argument('uri',help="database uri")
        init_.set_defaults(func=self.init)

        create_ = subparsers.add_parser('create',help="creates a new dropbox")
        create_.add_argument('uri',help="database uri")
        create_.add_argument('boxname')
        create_.add_argument('directory',help="directory to convert to dropbox",default=".")
        create_.set_defaults(func=self.create)

#clone_ = subparsers.add_parser('clone',help="create a new ltrbox out of an existing one")
#clone_.add_argument('src',help="source path")
#clone_.add_argument('dst',help="destination (default: .)",default=".")
#clone_.add_argument('boxname')
#clone_.set_defaults(func=self.clone)

        sync_ = subparsers.add_parser('sync',help="replicate database between box databases",\
        formatter_class=argparse.RawDescriptionHelpFormatter,\
        epilog =    "\nexamples:\n"\
                    "\tsync box-at-ther-host\n"\
                    "\tsync -d http://localhost:5984/myspace -D http://localhost:5984/myspace-backup\n"\
                    "\tsync -d http://localhost:5984/myspace box-at-other-host\n"\
            )
        sync_.add_argument('-d',"--dburi", help="database to use (overrides config)",default="",nargs="?")
        sync_.add_argument('-D',"--destination", help="database to use (overrides config)",default="",nargs="?")
        sync_.add_argument('boxname',help="boxname use when (default: .)",default=".",nargs="?")
        sync_.set_defaults(func=self.sync)

        fetch_ = subparsers.add_parser('fetch',help="copy wanted files from other ltrbox")
        fetch_.add_argument('-d',"--dburi", help="database to use (overrides config)",default="",nargs="?")
        fetch_.add_argument("-b",'--boxname',help="boxname (default: .)",default=".",required=False)
        fetch_.add_argument('src',help="source path")
        fetch_.add_argument('dst',help="destination (default: .)",default=".")
        fetch_.set_defaults(func=self.fetch)

        pull_ = subparsers.add_parser('pull',help="perform sync and fetch")
        pull_.add_argument('-d',"--dburi", help="database to sync to (overrides config)",default="",nargs="?")
        pull_.add_argument("-b",'--boxname',help="boxname (default: .)",default=".",required=False)
        pull_.add_argument('src',help="source path",nargs="?")
        pull_.add_argument('dst',help="destination (default: .)",default=".",nargs="?")
        pull_.set_defaults(func=self.pull)

        box_ = subparsers.add_parser('box',help="show list of ltrboxes in this volume")
        box_.set_defaults(func=self.box)

        ls_ = subparsers.add_parser('ls',help="show database filelist")
        ls_.add_argument('filespec',help="path (default: .)",default="",nargs="?")
        ls_.add_argument("-b",'--boxname',help="boxname (default: .)",default=".",required=False)
        ls_.set_defaults(func=self.ls)

        commit_ = subparsers.add_parser('commit',help="update database with filesystem")
        commit_.set_defaults(func=self.commit)

        status_ = subparsers.add_parser('status',help="compare filesystem to database")
        status_.set_defaults(func=self.status)

        diff_ = subparsers.add_parser('diff',help="compare files between boxes")
        diff_.add_argument('filespec',help="file to run compare on (default: .)",default=".")
        #FIXME: @box1 @box2 @box3
        diff_.add_argument('box1',help="first box for comparison (default: .)",default=".")
        diff_.add_argument('box2',help="second box for comparison")
        diff_.set_defaults(func=self.diff)

        show_ = subparsers.add_parser('show',help="show information on object")
        show_.add_argument('object',help="object (default: .)",default=".")
        show_.set_defaults(func=self.show)

        set_ = subparsers.add_parser('set',help="set object parameter")
        set_.add_argument('key',help="key (example: boxname.url)")
        set_.add_argument('value',help="value")
        set_.set_defaults(func=self.set)

        stat_ = subparsers.add_parser('stat',help="consult database about filename")
        stat_.add_argument("-b",'--boxname',help="boxname (default: .)",default=".",required=False)
        stat_.add_argument('filename')
        stat_.set_defaults(func=self.stat)

        args = parser.parse_args(argv)
        args.func(args)

    def init(self,args):
        uri = args.uri.strip()
        space = LtrSpace().createfromUri(uri)

    def create(self,args):
        uri = args.uri.strip()
        space = LtrSpace().setUri(uri)
        box = LtrBox(space).setUri(uri)
        box.setBoxname(args.boxname.strip())
        box.create()
        directory = args.directory.strip()
        box.fspath = directory
        box.writeCookie()

    def clone(self,args):
        name = args.boxname.strip()
        src = args.src.strip()
        dst = args.dst.strip()

        if os.path.isdir(src):
            srcbox = LtrSpace.boxFromCookie(src)
        else:
            space = LtrSpace().setUri(src)
            srcbox = space.getBox(space.boxname)
        
        dstbox = LtrBox(srcbox.space)
        dstbox.fspath = dst
        dstbox.setName(name)
        dstbox.create()
        dstbox.writeCookie()

    def commit(self,args):
        box = LtrSpace.boxFromCookie(os.getcwd())
        box.commit(dryrun=False)

    def diff(self,args):
        pass 

    def status(self,args):
        box = LtrSpace.boxFromCookie(os.getcwd())
        box.commit(dryrun=True)

    def show(self,args):
        box = LtrSpace.boxFromCookie(os.getcwd())
        print box.info(),

    def set(self,args):
        box = LtrSpace.boxFromCookie(os.getcwd())
        key = args.key.strip()
        value = args.value.strip()
        box.space.setopt(key,value)

    def stat(self,args):
        thisbox = LtrSpace.boxFromCookie(os.getcwd())
        fname = args.filename.strip()
        if args.boxname == ".":
            box = thisbox
        else:
            boxname = args.boxname
            box = thisbox.space.getBox(boxname)
            box.cwd = thisbox.cwd

        node = box.getNode(box.pathConv(fname))
        if node != None:
            print node.stat(),

    def sync(self,args):
        srcuri = LtrUri().setUri(args.dburi)
        if args.dburi != "":
            srcserver = couchdb.client.Server(srcuri.dbserveruri)
            (src,srcuri)= (srcuri,srcuri.spaceuri.rstrip("/"))
        else:
            thisbox = LtrSpace.boxFromCookie(os.getcwd())
            srcserver=thisbox.space.dbcursor
            src = thisbox.space
            srcuri = thisbox.space.spaceuri.rstrip("/")

        if hasattr(args,"destination"):
            # override boxname
            dst = LtrUri().setUri(args.destination)
            dsturi = dst.spaceuri.rstrip("/")
        elif hasattr(args,"boxname") and args.boxname != ".":
            #use dburi to lookup [args.boxname][dburi]
            box = srcserver[src.spacename][args.boxname]
            dsturi = box["couchurl"].rstrip("/")
        elif hasattr(args,"dst"):
            if args.dst == ".":
                dstdir = os.getcwd()
            else:
                dstdir = args.dst
            x= LtrSpace.boxFromCookie(dstdir)
            dsturi= x.space.spaceuri.rstrip("/")
        else:
            raise Exception

        if srcuri==dsturi:
            return
       
        print "ltr: sync %s %s" %(srcuri,dsturi)
        r = srcserver.replicate(srcuri,dsturi)
        import pprint
        if "no_changes" in r:
            print "Already up to date."
        else:
            #FIXME pretty print result
            pprint.pprint(r["history"][0])

    def pull(self,args):
        self.sync(args)
        self.fetch(args)

    def fetch(self,args):
        dst = os.getcwd()
        dstbox = LtrSpace.boxFromCookie(dst)
        if args.boxname != ".":
            #lookup sftp://path
            srcbox = dstbox.space.getBox(args.boxname)
            srcbox.fspath = srcbox.boxurl[len("sftp://localhost"):]
        else:
            src = args.src.strip()
            srcbox = LtrSpace.boxFromCookie(src,space=dstbox.space)

        dstbox.fetch(srcbox,dryrun=args.dryrun)

    def box(self,args):
        box = LtrSpace.boxFromCookie(os.getcwd())
        bn= box.space.getBoxNames()
        def check(test,compare):
            if test==compare:
                return "* "
            else:
                return "  "
        for boxname in bn:
            print check(boxname,box.id),boxname

    def ls(self,args):
        thisbox = LtrSpace.boxFromCookie(os.getcwd())
        #args.filespec
        if args.boxname == ".":
            box = thisbox
        else:
            boxname = args.boxname
            box = thisbox.space.getBox(boxname)
            box.cwd = thisbox.cwd
 
        f = box.getNode(box.pathConv(args.filespec))
        files = f.children(boxname=box.id)
        files = filter(lambda x: x.deleted!=True,files)
        filenames = map(lambda x: x.name,files)
        filenames.sort()
        print "\n".join(filenames),
