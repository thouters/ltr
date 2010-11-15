# Litter

*Filling the gap between Distributed Version Control Systems and rsync-style file synchronisation.*

I created Litter (`Ltr` henceforward) as a toolbox for file synchronisation like
Dropbox/Ubuntu One, yet using open technologies we've all come to love.

Ltr uses a filesystem crawler in python to keep track of the state of files in
a volume (`LtrSpace`).  This state is stored in a CouchDB replicated between the
hosts that have a check-out of the Space (a `LtrBox`).

This enables you to examine/navigate the directory listings of your disks,
when they are not mounted on your system.  This will allow for cunning
backup policies, a simple query can show which files don't have redundant
copies.

Each check-out of the Space has a `.ltr` file, containing the url
to the couchdb document containing LtrBox details.

A LtrSpace adheres to a policy, which specifies the behaviour of
`pull` operations.  A LtrBox can be set to only contain copies
of files marked to be on disk explicitly; `ondemand`, the complete
set of files in the space; `complete`, or only the bare directory
structure; `skeleton`

A couchapp (to be created) can allow for easy manipulation of the
list of pending operations for the next `pull`.

A centralised master-copy is easily implemented if desired.  A shell account
with a `complete` LtrBox, Ltr and CouchDB are sufficient.

Transporting large files between systems using a portable disk can be
streamlined by marking the relevant files as `requested` on the
portable disk and remote `LtrBox`, pulling the files into the LtrBox on
portable disk and later on pulling the files from portable disk
onto the destination system.

## Operations

* create http://user:pwd@dbhost:port/spacename/boxname folder
* clone  boxname /path/to/existing-box /path/to/new-box
* pull /path/to/another-box

