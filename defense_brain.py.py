import time
import os
import translations
import re

matrix = []
m = []
initialmap = createnewmap = westcomplete = northcomplete = c_x = c_y = 0
command = "none"


def getNextMessage(translator, buffer):
    complete, mData = translator.HasMessage(buffer)
    if not complete:
        return None, buffer
    mt, m, headers, hOff, bLen = mData
    body, buffer = buffer[hOff:hOff+bLen], buffer[hOff+bLen:]
    msg = translator.unmarshallFromNetwork(mt, m, headers, body)
    return msg, buffer

def createObjectDisplay(objectData, indent=""):
        s = ""
        for key, value in objectData:
            s += "{}{}: {}\n".format(indent, key, value)
        return s

def findcoord(scanResults):
    global c_x
    global c_y
    ss = "ControlPlaneObject-10007"
    for coord, objDataList in scanResults:
            obj = None
            for objData in objDataList:
                d = dict(objData)
                if d["type"] == "terrain":
                    terrain = d["identifier"]
                elif d["type"] == "object":
                    obj = createObjectDisplay(objData, indent="\t")
            if obj is not None:
                if ss in obj:
                    c_x,c_y = coord
                    #print ("************coordinates****************")
                    #print (c_x,c_y)


def createScanResultsDisplay2(scanResults):
    global m
    for coord, objDataList in scanResults:
        x,y = coord
        terrain = None
        obj = 0
        for objData in objDataList:
            d = dict(objData)
            #print ("dictionary d is",d)
            if d["type"] == "terrain":
                terrain = d["identifier"]
            elif d["type"] == "object":
                obj = 1
        if obj:
            m[y][x] = "O"
        elif terrain == "land":
            m[y][x] = "#"
        elif terrain == "water":
            m[y][x] = "="

    #print(matrix)   
    createMapResultDisplay(m[::-1])

 
def createMapResultDisplay(print_map):
    global map
    global m_x
    global m_y
    map = ""
    for i in range(4):
        for j in range(4):
            map += str(print_map[i][j])
        map += "\n"   
    #print(map)

def brainLoop():
    gameSocket = open("game://", "rb+")
#% TEMPLATE-ON
    ccSocketName = "default://20188.1.2054.6:35021"
#% TEMPLATE-OFF
    try:
        ccSocket = open(ccSocketName,"rb+")
    except:
        ccSocket = None

    loop = 0
    r = c = r1 = c1 = 0
    i = 1
    e = s = n = w = 0
    oc = []
    translator = translations.NetworkTranslator()
    hb = None
    gameDataStream = b""

    while True:
        loop += 1
        gameData = os.read(gameSocket.fileno(), 1024) # max of 1024
        gameDataStream += gameData
        if gameDataStream:
            msg, gameDataStream = getNextMessage(translator, gameDataStream)
            if isinstance(msg, translations.BrainConnectResponse):
                translator = translations.NetworkTranslator(*msg.attributes)
                hb = msg

        if (not gameData) and hb and (loop % 30 == 0) and ccSocket:
            # every thirty seconds, send heartbeat to cc
            try:
                os.write(ccSocket.fileno(), translator.marshallToNetwork(hb))
            except:
                ccSocket = None



        
        if isinstance(msg, translations.ScanResponse):
            findcoord(msg.scanResults)
            createScanResultsDisplay2(msg.scanResults)
        
        try:            
            if ccSocket:
                ccData = os.read(ccSocket.fileno(), 1024)
            else:
                ccData = b""
        except:
            ccData = b""
            ccSocket = None 

        if gameData and ccSocket:
            try: 
                os.write(ccSocket.fileno(), gameData)
            except:
                ccSocket = None

     	global command
        global c_x
        global c_y
        if ccData: os.write(gameSocket.fileno(), ccData)
        if (loop%5 == 0): 
            cmd = translations.ScanCommand()
            os.write(gameSocket.fileno(), translator.marshallToNetwork(cmd))
        
        if (loop%5 == 0):
            if m[c_y][c_x+1] == "O":
                command = "south-east"
                if m[c_y-1][c_x+1] == "O":
                    command = "south"

        if (loop%5 == 0):
            if m[c_y-1][c_x] == "O":
                command = "south-west"
                if m[c_y-1][c_x-1] == "O":
                    command = "west"
                
        if (loop%5 == 0):
            if m[c_y][c_x-1] == "O":
                command = "north-west"
                if m[c_y+1][c_x-1] == "O":
                    command = "north"
                
        
       if (loop%5 == 0):
             if m[c_y+1][c_x] == "O":
                 command = "north-east"
                 
       if command != "none":      
           os.write(gameSocket.fileno(), translator.marshallToNetwork(cmd)) 
        
        if not gameData and not gameDataStream and not ccData:
            time.sleep(.5) # sleep half a second every time there's no data
            
        if not ccSocket and loop % 60 == 0:
            # if the gamesock didn't open or is dead, try to reconnect
            # once per minute
            try:
                ccSocket = open(ccSocketName, "rb+")
            except:
                ccSocket = None

if __name__=="__main__":
    try:
        brainLoop()
    except Exception as e:
        print("Brain failed because {}".format(e))
        
        f = open("/tmp/error.txt","wb+")
        f.write(str(e).encode())
        f.close()

