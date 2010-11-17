# Litter

*Filling the gap between Distributed Version Control Systems and rsync-style file synchronisation.*

I created Litter (`Ltr` henceforward) to be the Dropbox/Ubuntu One of power
users, building on tools like ssh for network transparency.  And focussing
on a de-centralised topology.

Ltr uses a filesystem crawler in python to correlate local files 
against the index of the volume (the `LtrSpace`) to which they belong.

The only file operations ltr performs are ls, stat, file --mime, sha1sum, copy,
rm, mv.  No copies of your files, other than the ones you work on in (various)
LtrBox-es are kept behind the scenes or in databases (yes, very much unlike svn
and git).

A `LtrBox` is such a local checkout of the LtrSpace, and contains some
or all files in the LtrSpace.  The state of all LtrBox-es is stored in a
CouchDB database, which is replicated between the LtrBox-keeping hosts.

The mobile file index allows you to examine/navigate the directory listings of
your disks, when they are not mounted on your system.  This way you have 
the indexes of backup disks at hand, and a simple query can show which files
don't have any redundant copies.

Each LtrBox has a `.ltr` file, containing the url to the couchdb document
containing LtrBox details.

A LtrSpace adheres to a policy which specifies the behaviour of `pull`
operations.  A LtrBox can have on of three policies set: 

* `ondemand`: only pull-in copies of files which are marked to be in said Box explicitly
* `complete`: try to obtain all files in the Space
* `skeleton`: at least create the bare directory structure (can be built from database)

A couchapp (to be created) can allow for easy manipulation of the
list of pending operations for the next `pull`.

A centralised master-copy repository is easily implemented if desired.  A shell
account with a `complete` LtrBox, Ltr and CouchDB are sufficient.

Transporting large files between systems using a portable disk can be
streamlined by marking the relevant files as `requested` on the
portable disk and remote `LtrBox`, pulling the files into the LtrBox on
portable disk and later on pulling the files from portable disk
onto the destination system.

## Operations

* create http://user:pwd@dbhost:port/spacename/boxname folder
* clone  boxname /path/to/existing-box /path/to/new-box
* pull user@host:/path/to/another-box

## Roadmap

* checking off the TODO file
* using pamaramiko for network transparency (ssh)
* moving to python-twisted 
