CREATE_GAME_TABLE = "CREATE TABLE IF NOT EXISTS %(gameID)s (ID INTEGER PRIMARY KEY AUTOINCREMENT, USERID TINYTEXT, LAT TINYTEXT, LON TINYTEXT, TIME TINYTEXT, STATE TINYTEXT)"
CREATE_USER_NAMES_TABLE = "CREATE TABLE IF NOT EXISTS USERNAMES (uID TINYTEXT, name TINYTEXT, gameID TINYTEXT,regtime TINYTEXT)"
CREATE_GAME_NAMES_TABLE = "CREATE TABLE IF NOT EXISTS GAMESINFO (gameID TINYTEXT, name TINYTEXT, options TINYTEXT, regtime TINYTEXT)"
ADD_GAME_INFO     = "INSERT INTO GAMESINFO VALUES (\"%(gameID)s\", \"%(name)s\", \"%(settings)s\", \"%(regtime)s\")"
ADD_USER_DATA     = "INSERT INTO USERNAMES VALUES(\"%(uID)s\", \"%(name)s\", \"%(gameID)s\", \"%(regtime)s\")"
ADD_GAME_DATA     = "INSERT INTO %(gameID)s VALUES (NULL ,\"%(userID)s\", \"%(lat)s\", \"%(lon)s\", \"%(time)s\", \"%(state)s\")"
GET_MAX_ID        = "SELECT MAX(ID) FROM %(gameID)s"

MAX_WRITES = 10

class VeloGameDatabase:

    def __init__(self, dbFileName):
        import sqlite3
        self.db = sqlite3.connect("database/" + dbFileName)
        self.cur = self.db.cursor()
        self.cur.execute(CREATE_USER_NAMES_TABLE)
        self.cur.execute(CREATE_GAME_NAMES_TABLE)
        self.writesCount = 0


    def createGameTable(self, gameID):
        self.cur.execute(CREATE_GAME_TABLE % {"gameID":gameID})
        self.writesCount += 1
        if self.writesCount > MAX_WRITES:
            self.db.commit()
            self.writesCount = 0


    def addGameInfo(self, gameID, gameData):
        name, regtime, settings = gameData
        self.cur.execute(ADD_GAME_INFO % {"gameID":gameID, "name":name, "settings":str(settings), "regtime":str(regtime)})
        self.writesCount += 1
        if self.writesCount > MAX_WRITES:
            self.db.commit()
            self.writesCount = 0


    def closeDB(self):
        self.db.commit()
        self.db.close()
        
    
    def addRawData(self, gameID, UserIDLatLonTimeStateList):
        userID, lat, lon, time, state = UserIDLatLonTimeStateList
        self.cur.execute(ADD_GAME_DATA % {"gameID":gameID, "id":self.getMaxTableID(gameID), "userID":userID, "lat":lat, "lon":lon, "time":time, "state":state})
        self.writesCount += 1
        if self.writesCount > MAX_WRITES:
            self.db.commit()
            self.writesCount = 0
            

    def addUserData(self, uID, name, gameID,regtime):
        self.cur.execute(ADD_USER_DATA % {"uID":uID, "name":name, "gameID":gameID,"regtime":regtime})
        self.writesCount += 1
        if self.writesCount > MAX_WRITES:
            self.db.commit()
            self.writesCount = 0
            

    def getLastUserCoords(self, gameID, userID):
        GET_USER_DATA_ID = "SELECT ID FROM \"%(gameID)s\" WHERE USERID=\"%(userID)s\""
        GET_DATA_BY_ID = "SELECT * FROM \"%(gameID)s\" WHERE ID=\"%(id)s\""
        self.cur.execute(GET_USER_DATA_ID % {"gameID":gameID, "userID":userID})
        ids = self.cur.fetchall()
        if ids:
            self.cur.execute(GET_DATA_BY_ID % {"gameID":gameID, "id":ids[-1][0]})
            data = self.cur.fetchall()
            if data:
                return data[0]
            else:
                return None
        else:
            return None
    
        
        
        
        
    def exportGame(self, gameID):
        pass
                         

    def getMaxTableID(self, gameID):
        self.cur.execute(GET_MAX_ID % {"gameID":gameID})
        maxID = self.cur.fetchone()
        if maxID[0] == None:
            return 0
        else:
            return (maxID[0] + 1)

##VG = VeloGameDatabase("velogames.db")
##VG.getLastUserCoords("Ge5f551d5b8e1ee80d797500349dd583a90d643e3", "-6904113067144871861")

