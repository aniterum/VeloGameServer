CREATE_GAME_TABLE = "CREATE TABLE IF NOT EXISTS %(gameID)s (ID UNSIGNED INT, USERID TINYTEXT, LAT TINYTEXT, LON TINYTEXT, TIME TINYTEXT)"
ADD_GAME_DATA     = "INSERT INTO %(gameID)s VALUES (%(id)i ,\"%(userID)s\", \"%(lat)s\", \"%(lon)s\", \"%(time)s\")"
GET_MAX_ID        = "SELECT MAX(ID) FROM %(gameID)s"

class VeloGameDatabase:

    def __init__(self, dbFileName):
        import sqlite3
        self.db = sqlite3.connect("database/" + dbFileName)
        self.cur = self.db.cursor()


    def createGameTable(self, gameID):
        self.cur.execute(CREATE_GAME_TABLE % {"gameID":gameID})


    def closeDB(self):
        self.db.commit()
        self.db.close()
        
    
    def addRawData(self, gameID, data):
        splitted = data.decode().split("|")
        self.cur.execute(ADD_GAME_DATA % {"id":self.getMaxTableID(gameID),"gameID":gameID, "userID":splitted[0], "lat":splitted[1], "lon":splitted[2], "time":splitted[3]})
        
        
    def exportGame(self):
        pass

    def getMaxTableID(self, gameID):
        self.cur.execute(GET_MAX_ID % {"gameID":gameID})
        maxID = self.cur.fetchone()
        if maxID[0] == None:
            return 0
        else:
            return (maxID[0] + 1)
                         

#ТЕСТ записи в базу данных
if __name__ == '__main__':
    d = b"userID|432.123|44.323|1407265320.4782007"
    VG = VeloGameDatabase("db.db")
    VG.createGameTable("GAMEID")
    VG.addRawData("GAMEID", d)
    VG.addRawData("GAMEID", d)
    VG.addRawData("GAMEID", d)
    VG.closeDB()

