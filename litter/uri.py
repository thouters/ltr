import unittest

class LtrUri:
    def __init__(self):
        self.dbservername = False
        self.dbserveruri = False
        self.spacename = False
        self.spaceuri = False
        self.boxname = False
        self.boxuri = False

    def setUri(self,uri):
        pieces = uri.split("/")
        if len(pieces):
            self.http = pieces.pop(0)
        if len(pieces):
            slashslash = pieces.pop(0)
        if len(pieces):
            self.setDbservername(pieces.pop(0))
        if len(pieces):
            self.setSpacename(pieces.pop(0))
        if len(pieces):
            self.setBoxname(pieces.pop(0))

        return self

    def setDbservername(self,dbservername):
        self.dbservername = dbservername
        self.dbserveruri = self.http + "//" + self.dbservername +"/"
    def setSpacename(self,spacename):
        self.spacename = spacename
        self.spaceuri = self.dbserveruri+self.spacename+"/"
    def setBoxname(self,boxname):
        self.boxname = boxname
        self.boxuri = self.spaceuri+self.boxname


class LtrContextTest(unittest.TestCase):
    def test1(self):
        u = LtrUri().setUri("http://localhost:5984/dbname/boxname")
        self.assertEqual(u.dbserveruri,"http://localhost:5984/")
        self.assertEqual(u.spaceuri,"http://localhost:5984/dbname/")
        self.assertEqual(u.boxuri,"http://localhost:5984/dbname/boxname")
        self.assertEqual(u.dbservername,"localhost:5984")
        self.assertEqual(u.spacename,"dbname")
        self.assertEqual(u.boxname,"boxname")

if __name__=="__main__":
    unittest.main()
