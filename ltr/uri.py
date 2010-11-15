import unittest
import couchdb
from .space import LtrSpace
class LtrUri:
    dbservername = False
    dbserveruri = False
    spacename = False
    spaceuri = False
    boxname = False
    boxuri = False
    dbcursor = False
    db = False
    
    def __init__(self,uristr):
        pieces = uristr.split("/")
        if len(pieces):
            http = pieces.pop(0)
        if len(pieces):
            slashslash = pieces.pop(0)
        if len(pieces):
            self.dbservername = pieces.pop(0)
            self.dbserveruri = http + "//" + self.dbservername +"/"
        if len(pieces):
            self.spacename = pieces.pop(0)
            self.spaceuri = self.dbserveruri+self.spacename+"/"
        if len(pieces):
            self.boxname = pieces.pop(0)
            self.boxuri = self.spaceuri+self.boxname

    def connectDatabaseServer(self):
        print "ltr: connect", self.dbserveruri
        self.dbcursor = couchdb.Server(self.dbserveruri)

    def getCursor(self):
        if not self.dbcursor:
            self.connectDatabaseServer()
        return self.dbcursor

class LtrUriTest(unittest.TestCase):
    def test1(self):
        u = LtrUri("http://localhost:5984/dbname/boxname")
        self.assertEqual(u.dbserveruri,"http://localhost:5984")
        self.assertEqual(u.spaceuri,"http://localhost:5984/dbname")
        self.assertEqual(u.boxuri,"http://localhost:5984/dbname/boxname")
        self.assertEqual(u.dbservername,"localhost:5984")
        self.assertEqual(u.spacename,"dbname")
        self.assertEqual(u.boxname,"boxname")

if __name__=="__main__":
    unittest.main()
