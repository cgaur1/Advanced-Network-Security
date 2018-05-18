import time
import os
import translations
import re

matrix = []
m = []
initialmap = createnewmap = westcomplete = northcomplete = c_x = c_y = 0
command = "west"


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

def createScanResultsDisplay(scanResults):
    global matrix
    for coord, objDataList in scanResults:
        x,y = coord
        terrain = None
        obj = 0
        for objData in objDataList:
            d = dict(objData)
            if d["type"] == "terrain":
                terrain = d["identifier"]
            elif d["type"] == "object":
                obj = 1
        if obj:
            matrix[y][x] = "O"
        elif terrain == "land":
            matrix[y][x] = "#"
        elif terrain == "water":
            matrix[y][x] = "="

    #print(matrix)   
    createMapResultDisplay(matrix[::-1])

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
    for i in range(100):
        for j in range(100):
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
            substring = "Could not"
            global westcomplete
            global northcomplete
            global m_x
            global m_y
            global command
            if isinstance(msg, translations.MoveCompleteEvent):
                if substring in msg.message:
                    if westcomplete == 0:
                        westcomplete = 1
                        command = "north"
                        print ("westcomplete")
                    elif northcomplete == 0 and westcomplete == 1 and c_y == 99:
                        print ("********REACHING HERE*******************")
                        northcomplete = 1
                        oc = re.findall(r'\d+', msg.message)
                        m_x = int(oc[-2])
                        m_y = int(oc[-1])
                        r = (m_x - c_x) - 1
                        r1 = m_x - 1
                        c = m_y - 1
                        c1 = m_y - 4
                        #print (r)
                        #print ("East Move Value")
 
                    #print (coordinates)

        if (not gameData) and hb and (loop % 30 == 0) and ccSocket:
            # every thirty seconds, send heartbeat to cc
            try:
                os.write(ccSocket.fileno(), translator.marshallToNetwork(hb))
            except:
                ccSocket = None


        global initialmap
        global matrix
        if not initialmap:
            for i in range(100):
                row = []
                for j in range(100):
                    row.append("0")
                matrix.append(row)
            #print (matrix)
            initialmap = 1

        global createnewmap
        global m
        if northcomplete and not createnewmap:
            for i in range(m_x):
                row = []
                for j in range(m_y):
                    row.append("0")
                m.append(row)
            #print (m)
            createnewmap = 1 
        
        if initialmap:
            if isinstance(msg, translations.ScanResponse):
                findcoord(msg.scanResults)
                if not northcomplete:
                    createScanResultsDisplay(msg.scanResults)
                else:
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
        global westcomplete
        global northcomplete
        global command
        global c_x
        global c_y
        if ccData: os.write(gameSocket.fileno(), ccData)
        if (loop%5 == 0): 
            cmd = translations.ScanCommand()
            os.write(gameSocket.fileno(), translator.marshallToNetwork(cmd))
        if (loop%15 == 0 and northcomplete == 0 and westcomplete == 0):
            #print ("current value"+matrix[c_y][c_x])
            #print ("check value"+matrix[c_y][c_x-1])
            if c_x > 0:
                if matrix[c_y][c_x-1] == "O":
                    cmd = translations.MoveCommand("north-west")
                else:
                    cmd = translations.MoveCommand(command)
            else:
                cmd = translations.MoveCommand(command)
            os.write(gameSocket.fileno(), translator.marshallToNetwork(cmd))
        if (loop%15 == 0 and northcomplete == 0 and westcomplete == 1):
            if c_y < 99:
                #print ("going north")
                #print (t_x,t_y)
                #print ("current value"+matrix[c_y][c_x])
                #print ("check value"+matrix[c_y+1][c_x])
                if matrix[c_y+1][c_x] == "O":
                    cmd = translations.MoveCommand("north-east")
                    #print ("*************************GOING NE******************************")
                else:
                    cmd = translations.MoveCommand(command)
            else:
                cmd = translations.MoveCommand(command)
            os.write(gameSocket.fileno(), translator.marshallToNetwork(cmd))
        if (loop%20 == 0 and northcomplete == 1 and westcomplete == 1):
            e = 1
            northcomplete += 1
        if (loop%20 == 0 and  r > 0 and e <= r and e):
            e+=1
            #print ("going east")
            #print (t_x,t_y)
            #print ("current value"+m[c_y][c_x])
            #print ("check value"+m[c_y][c_x+1])
            if m[c_y][c_x+1] == "O":
                cmd = translations.MoveCommand("south-east")
                c -=1
            else:
                cmd = translations.MoveCommand("east")
            os.write(gameSocket.fileno(), translator.marshallToNetwork(cmd)) 
        if (loop%20 == 0 and e > r and r > 0):
            e = 0
            s = 1 
        if (loop%15 == 0 and s <= c and c > 0 and s):
            s += 1
            #print ("going south")
            #print (t_x,t_y)
            #print ("current value"+m[c_y][c_x])
            #print ("check value"+m[c_y-1][c_x])
            if m[c_y-1][c_x] == "O":
                cmd = translations.MoveCommand("south-west")
                r1 -=1
            else:
                cmd = translations.MoveCommand("south")
            os.write(gameSocket.fileno(), translator.marshallToNetwork(cmd))
        if (loop%20 == 0 and s > c and c > 0):
            s = 0
            w = 1
        if (loop%15 == 0 and w <= r1 and r1 > 0 and w):
            w+=1
            #print ("going west")
            #print (t_x,t_y)
            #print ("current value"+m[c_y][c_x])
            #print ("check value"+m[c_y][c_x-1])
            if m[c_y][c_x-1] == "O":
                cmd = translations.MoveCommand("north-west")
                c1 -=1
            else:
                cmd = translations.MoveCommand("west")
            os.write(gameSocket.fileno(), translator.marshallToNetwork(cmd))
        if (loop%20 == 0 and w > r1 and r1 > 0):
             w = 0
             n = 1
        if (loop%15 == 0 and n <= c1 and c1 > 0 and n):
             n += 1
             #print ("going north")
             #print (t_x,t_y)
             #print ("current value"+m[c_y][c_x])
             #print ("check value"+m[c_y+1][c_x])
             if m[c_y+1][c_x] == "O":
                 cmd = translations.MoveCommand("north-east")
                 #print ("***********************going north east********************")
             else:
                 cmd = translations.MoveCommand("north")
             os.write(gameSocket.fileno(), translator.marshallToNetwork(cmd)) 
        if (loop%20 == 0 and n > c1 and c1 > 0):
             n = 0
             e = 1
             r = c1
             r1 = c1 - 3
             c = c1-3
             #print ("south and west distance")
             #print (r,r1,c)
             c1 -= 4
        
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

