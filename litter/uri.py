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

        return self


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
