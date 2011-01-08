#!/usr/bin/env python
from space import LtrSpace
from box import LtrBox
import os
import argparse
import sys

class LtrCli:
    def __init__(self,argv):
        if argv==[]:
            argv=["status"]
        parser = argparse.ArgumentParser(\
            description="ltr - Decentralised personal file distribution",\
            prog='ltr')
        parser.add_argument('-n','--dryrun',help='dryrun',action="store_true")

        subparsers = parser.add_subparsers(title="commands")

        default_create_uri = "http://localhost:5984/databasename/boxname"

        create_ = subparsers.add_parser('create',help="creates a new dropbox")
        create_.add_argument('uri',help="database uri (default: {0})".format(default_create_uri),default=default_create_uri)
        create_.add_argument('directory',help="directory to convert to dropbox",default=".")
        create_.set_defaults(func=self.create)

        clone_ = subparsers.add_parser('clone',help="create a new ltrbox out of an existing one")
        clone_.add_argument('src',help="source path")
        clone_.add_argument('dst',help="destination (default: .)",default=".")
        clone_.add_argument('boxname')
        clone_.set_defaults(func=self.clone)

        pull_ = subparsers.add_parser('pull',help="retrieve wanted files from other ltrbox")
        pull_.add_argument('src',help="source path")
        pull_.add_argument('dst',help="destination (default: .)",default=".")
        pull_.set_defaults(func=self.pull)

        box_ = subparsers.add_parser('box',help="show list of ltrboxes in this volume")
        box_.set_defaults(func=self.box)

        ls_ = subparsers.add_parser('ls',help="show database filelist")
        ls_.add_argument('filespec',help="path (default: .)",default=".")
        ls_.add_argument("-b",'--boxname',help="boxname (default: .)",default=".", action="append")
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
        stat_.add_argument('filename')
        stat_.set_defaults(func=self.stat)

        args = parser.parse_args(argv)
        args.func(args)

    def create(self,args):
        uri = args.uri.strip()
        directory = args.directory.strip()
        space = LtrSpace().createfromUri(uri)
        box = LtrBox(space).setUri(uri)
        box.create()
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
        box = LtrSpace.boxFromCookie(os.getcwd())
        fname = args.filespec.strip()
        node = box.getDrop(box.pathConv(fname))
        if node != None:
            print node.stat(),

    def pull(self,args):
        dst = os.getcwd()
        src = args.src.strip()
        dstbox = LtrSpace.boxFromCookie(dst)
        srcbox = LtrSpace.boxFromCookie(src,space=dstbox.space)

        dstbox.pull(srcbox,dryrun=args.dryrun)

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
 
        f = box.getDrop(box.pathConv(""))
        print "\n".join(map(lambda x: x.name, f.children()))
