# Litter

Decentralised personal file distribution (on a redundant array of inexpensive laptops and archive disks).

I created Litter (`Ltr` henceforward) to be a more personal Dropbox/UbuntuOne/... .
Initially targetted at power users, built to feel familiar for shell users.
For instance it uses user@host:/path uri's and ssh for network file access.

Ltr uses a filesystem crawler in python to correlate files from a local folder
against the index of the volume (the `LtrSpace`) to which they belong.

A `LtrBox` is such an instance of a LtrSpace, and contains some or all files in
the LtrSpace.  The state of all LtrBox-es is stored in a CouchDB database,
which is replicated between the LtrBox-keeping hosts.

The only file operations ltr performs are ls, stat, file --mime, sha1sum, copy,
rm, mv.  No copies of your files, other than the ones you work on in (various)
LtrBox-es are kept behind the scenes or in databases, which is very unlike
svn and git).


Having the full file index on every host allows you to examine/navigate the
directory listings of your disks, when they are not mounted on your system.
This way you have the indexes of backup disks at hand, and a simple query can
show which files don't have any redundant copies.

Each LtrBox has a `.ltr` file, containing the url to the couchdb document
containing LtrBox details.

A LtrBox adheres to a policy which specifies the behaviour of `pull`
operations.  A LtrBox can have on of three policies set: 

* `ondemand`: only pull-in files which are marked to be in the LtrBox explicitly
* `complete`: all files in the space are wanted
* `skeleton`: as a minimum, retain the bare directory structure of the space on-disk.

A couchapp (to be created) can allow for easy manipulation of the
list of pending operations for the next `pull`.

A centralised repository is easily implemented if desired.  A shell
account with a `complete` LtrBox, Ltr and CouchDB are sufficient.

Transporting large files between systems using a thumbdrive can be
streamlined like this:

* mark the desired files as `requested` on a thumbdrive
* mark the desired files as `requested` on the remote `LtrBox`
* pull the files onto thumbdrive  
* physically move thumbdrive to destination
* mount and pull the files from thumbdrive to the destination system.

## Operations

    thomas@maytag 1b % ltr --help
    usage: ltr [-h] [-n]
               {box,pull,stat,set,show,create,status,ls,diff,commit,clone} ...
    
    ltr - Decentralised personal file distribution
    
    optional arguments:
      -h, --help            show this help message and exit
      -n, --dryrun          dryrun
    
    commands:
      {box,pull,stat,set,show,create,status,ls,diff,commit,clone}
        create              creates a new dropbox
        clone               create a new ltrbox out of an existing one
        pull                retrieve wanted files from other ltrbox
        box                 show list of ltrboxes in this volume
        ls                  show database filelist
        commit              update database with filesystem
        status              compare filesystem to database
        diff                compare files between boxes
        show                show information on object
        set                 set object parameter
        stat                consult database about filename

### Create LtrSpace and box

    thomas@maytag ~ % ltr init http://thomas:geheim@maytag:5984/testspace
    ltr: create database  testspace
    ltr: push design docs  testspace
    thomas@maytag ~ % mkdir xyz; cd xyz
    thomas@maytag ~ % ltr create http://thomas:geheim@maytag:5984/testspace box@maytag .
    ltr: new box to database  <ltrbox testspace/box@maytag >
    ltr: wrote cookie for box@maytag

### ltr status

    thomas@maytag xyz % touch abc def
    thomas@maytag xyz % cp ~/0385730624.pdf .
    thomas@maytag xyz % mkdir subdir1
    thomas@maytag xyz % cp ../maximus_0.4.14.orig.tar.gz subdir1
    thomas@maytag xyz % ltr status
    N /abc
    N /def
    N /subdir1
    N /notes.html
    N /subdir1/maximus_0.4.14.orig.tar.gz


info:

* N New
* C copy in sync (hidden from display by default)
* M modified
* D discarded (removed from box)
* W wanted (awaiting fetch)
* L lost (last copy disapeared)

flags:

* s skip (marked skip or deleted on this disk by user, not automatically fetched)
* p purge from space (ltr rm)
* c copy present in box
* b box

### ltr commit

    thomas@maytag xyz % ltr commit
    N /abc
    N /def
    N /subdir1
    N /notes.html
    N /subdir1/maximus_0.4.14.orig.tar.gz
    .....
    thomas@maytag xyz %

### clone box
    (actions performed on different computer)
    thomas@bauknecht ~ % ltr init http://thomas:geheim@bauknecht:5984/testspace
    ltr: create database  testspace
    ltr: push design docs  testspace
    thomas@bauknecht ~ % ltr sync -d http://thomas:geheim@maytag:5984/testspace -D http://thomas:geheim@bauknecht:5984/testspace
    ltr: sync http://thomas:geheim@localhost:5984/x1 http://thomas:geheim@localhost:5984/x2
    {'doc_write_failures': 0,
    'docs_read': 14,
    'docs_written': 14,
    'end_last_seq': 15,
    'end_time': 'Mon, 17 Jan 2011 22:31:59 GMT',
    'missing_checked': 0,
    'missing_found': 14,
    'recorded_seq': 15,
    'session_id': '620c1a75f8307b30a43ba4b6671a465b',
    'start_last_seq': 0,
    'start_time': 'Mon, 17 Jan 2011 22:31:58 GMT'}
    thomas@bauknecht ~ % cd mkdir box2dir; cd box2dir
    thomas@bauknecht box2dir % ltr create http://thomas:geheim@bauknecht:5984/testspace box@bauknecht .
    ltr: new box to database  <ltrbox testspace/box@bauknecht >
    ltr: wrote cookie for  box@bauknecht
    thomas@maytag box2dir % ltr
    w /abc
    w /def
    w /notes.html
    w /subdir1


### pull user@host:/path/to/another-box

    thomas@bauknecht box2dir % ltr pull box@maytag
    ltr: pull  box@maytag
    scp sftp://thomas@maytag/.../xyz/notes.html /home/thomas/box2dir/notes.html
    scp sftp://thomas@maytag/.../xyz/def /home/thomas/box2dir/def
    mkdir /home/thomas/box2dir/subdir1
    scp sftp://thomas@maytag/.../xyz/subdir1/maximus_0.4.14.orig.tar.gz /home/thomas/box2dir/subdir1
    scp sftp://thomas@maytag/.../xyz/abc /home/thomas/box2dir/abc
    ....
    thomas@maytag box2dir % 

## Roadmap

* checking off the TODO file
* using python-paramiko for network transparency (ssh)
* moving to python-twisted 
