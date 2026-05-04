#VRCHAT PLURAL CHATBOX Library by krismastime Version 1.4


# Coded by krismastime (https://github.com/krismastime)
# Globals and their default values

global timeformat, pingtime, frontID, frontStart, message, chatbox, chatboxVisibility, timerVisibility, afk, aloop, vrc_loggedin, ip, port, client, taskcancelled
timeformat = "digital"
pingtime = time.time()
frontID = []
frontStart = []
message = ""
chatbox = ""
timerVisibility = False
afk = False
aloop = ""
vrc_loggedin = False
ip = "127.0.0.1"
port = 9000
client = udp_client.SimpleUDPClient(ip,port)
taskcancelled = False

def get_vk(key):
    return key.vk if hasattr(key, "vk") else key.value.vk

def on_press(key):
    vk = get_vk(key)
    new_kb.add(vk)

def on_release():
    return False

def set_kb():
    global new_kb
    new_kb = set()
    with keyboard.Listener(on_press=on_press,on_release=on_release) as listener:
        listener.join()
    return new_kb



async def ping(hostname,ws):
    while True:
        try:
            global pingtime
            pingtime = time.time()
            await ws.send("ping")
            await asyncio.sleep(10)
        except Exception as e:
            print("Error in ping")
            print(e)
            await asyncio.sleep(5)

def add_front(message,settings,logger):
    global frontID, frontStart
    try:
        frontUpd = json.loads(message)
        frontUpd = frontUpd["results"][0]["content"]
        frontID.append(frontUpd["member"])
        frontStart.append(int(frontUpd["startTime"])/1000)
        logger.emit(str("Member "+settings["memberdict"][frontID[-1]]["name"]+" began fronting at ")+str(datetime.fromtimestamp(frontStart[-1])))
        update_avatar(settings)
    except Exception as e:
        print(e)

def remove_front(message,settings,logger):
    global frontID, frontStart
    try:
        frontUpd = json.loads(message)
        frontUpd = frontUpd["results"][0]["content"]
        list_index = frontID.index(frontUpd["member"])
        logger.emit(str("Member "+settings["memberdict"][frontID[list_index]]["name"]+" stopped fronting at ")+str(datetime.fromtimestamp(int(frontUpd["endTime"])/1000)))
        frontID.pop(list_index)
        frontStart.pop(list_index)
    except Exception as e:
        print(e)

async def listen(hostname,ws,settings,logger):    
    while True:
        global message
        message = await ws.recv()
        try:
            if message == "pong":
                logger.emit(str("Ping-ponged: "+str(int((time.time()-pingtime)*1000))+"ms"))
            elif "insert" in message:
                add_front(message,settings,logger)
            elif "endTime" in message:
                remove_front(message,settings,logger)
            else:
                logger.emit(message)
        except Exception as e:
            print("Error in listen")
            print(e)
            await asyncio.sleep(1)

def manual_update(settings):
    frontID, frontStart = asyncio.run(get_fronter(settings["sp_token"]))
    for i in len(frontID):
        messageManual = {"results":[{"content":{"member":frontID[i],"startTime":frontStart[i]*1000}}]}
        messageManual = json.dumps(messageManual)
        print(messageManual)
        add_front(messageManual)

async def cancelcheck():
    while True:
        if taskcancelled == True:
            raise TerminateTG()
        await asyncio.sleep(1)

async def get_fronter(readToken):
    global frontID, frontStart
    conn = http.client.HTTPSConnection("api.apparyllis.com")
    payload = ''
    headers = {
    'Authorization': readToken
    }
    conn.request("GET", "/v1/fronters/", payload, headers)
    res = conn.getresponse()
    res = res.read()[1:-1]
    res = json.loads(res.decode("utf-8"))
    for i in res:
        if i == "content":
            frontStart.append(float(res[i]["startTime"])/1000)
            frontID.append(res[i]["member"])
    return frontID, frontStart

def as_list(pairs):
    return list(pairs)

def time_text(whenfrom,timeformat):
    now = time.time()
    timespan = int(abs(now - (whenfrom)))
    delta = timedelta(seconds=timespan)
    if timeformat == "digital":
        fronttimespan = delta
    else:
        if timespan < 60:
            fronttimespan = "less than a minute"
        elif timespan > 60 and timespan < 3600:
            fronttimespan = str(timespan//60)+" mins"
        else:
            fronttimespan = str(timespan//3600)+" hrs "+str((timespan//60)-((timespan//3600)*60))+" mins"
    return str(fronttimespan)

def chat_format(i,fronters,pronouns):
    return i.replace("#fronter",fronters).replace("#pronouns",pronouns).replace("#time",time_text(max(frontStart),timeformat))

async def chatbox_string(settings,chatbox_preview):
    global chatbox
    while True:
        fronters, pronouns = "", ""
        try:
            if len(frontID) == 1:
                fronters = str(settings["memberdict"][frontID[0]]["name"])
                pronouns = str(settings["memberdict"][frontID[0]]["pronouns"])         
            else:
                for i in frontID:
                    fronters = str(fronters+settings["memberdict"][i]["name"]+"|") 
                    pronouns = str(pronouns+settings["memberdict"][i]["pronouns"]+"|")
        except:
            print("Could not parse get fronters or pronouns.")
        try:
            if chatboxVisibility == True:
                if afk == False:
                    if timerVisibility == True and timeformat == "digital":
                        chatbox = chat_format(settings["chatbox"]["time_digital"],fronters,pronouns)
                    elif timerVisibility == True and timeformat != "digital":
                        chatbox = chat_format(settings["chatbox"]["time_full"],fronters,pronouns)
                    else:
                        chatbox = chat_format(settings["chatbox"]["generic"],fronters,pronouns)
                else:
                    chatbox = chat_format(settings["chatbox"]["afk"],fronters,pronouns)
            else:
                chatbox = ""
        except Exception as e:
            print("Could not parse chatbox string.")
            print(e)
        chatbox_preview.emit(chatbox)
        await asyncio.sleep(1)

async def status_string(settings):
    global aloop, frontID

    try:
        current_user = vrc_login.current_user
        user_var = vrc_login.user_var
        while True:
            try:
                await asyncio.sleep(70)
                status = settings["chatbox"]["status"] #Edit this to allow for more than 1 fronter, frontID is a list, check for list length
                status = status.replace("#fronter",str(settings["memberdict"][frontID[0]]["name"])).replace("#pronouns",str(settings["memberdict"][frontID[0]]["pronouns"]))
                request = {'statusDescription':status}
                print(request)
                user_var.update_user(user_id=settings["vrc_info"]["vrc_userid"],update_user_request=request)
            except Exception as e:
                print(e)
                await asyncio.sleep(10)
    except:
        print("Lost connection to VRChat API")

async def create_websocket(hostname,payload,settings,logger):
    global message,systemID
    i = 0
    ws = await websockets.connect(hostname)
    while i < 5:
        i+=1
        await ws.send(payload)
        message = await ws.recv()
        if "Successful" in message:
            logger.emit("Connected to SimplyPlural")
            try:
                message = json.loads(message)
                systemID = message["resolvedToken"]["uid"]
                logger.emit("Socket created with system ID "+systemID)
                return ws, systemID
            except:
                logger.emit("Unable to parse system ID.")
        if i == 5 and settings["attempt_reconnect"] == False:
            logger.emit("Unable to connect to SimplyPlural. Is the read token valid?")
        elif i == 5 and settings["attempt_reconnect"] == True:
            logger.emit("Unable to connect to SimplyPlural. Retrying in 10s.")
            await asyncio.sleep(10)
            i = 0
            continue
        else:
            logger.emit("\nRetrying ("+str(i)+")")
            await asyncio.sleep(1)
    systemID = ""
    return ws, systemID

async def gather_member_info(settings,logger):
    try:
        frontID, frontStart = await get_fronter(settings["sp_token"])
        return frontID, frontStart
    except:
        logger.emit("Unable to gather member details from SimplyPlural.")
        return "",""

async def get_member_details(systemID,readToken):
    conn = http.client.HTTPSConnection("api.apparyllis.com")
    memberdict = {}
    payload = ''
    headers = {
    'Authorization': readToken
    }
    conn.request("GET", "/v1/members/"+systemID, payload, headers)
    res = conn.getresponse()
    memberjson = res.read()
    memberlist = json.loads((memberjson.decode("utf-8")),object_pairs_hook=as_list)
    for x in memberlist:
        for y in x:
            if y[0] == "id":
                a = y[1]
            if y[0] == "content":
                for z in y[1]:
                    if z[0] == "name":
                        b = z[1]
                    elif z[0] == "pronouns":
                        c = z[1]
        memberdict[a] = [b,c]
    return memberdict

async def auth(settings,chatbox_preview,logger):
    global systemID, frontID, frontStart, chatboxVisibility,taskcancelled

    taskcancelled = False
    chatboxVisibility = settings["visible_on_load"]

    hostname = "wss://api.apparyllis.com/v1/socket"
    payload = json.dumps({"op": "authenticate", "token": settings["sp_token"]})

    ws, systemID = await create_websocket(hostname,payload,settings,logger)
    
    frontID, frontStart = await gather_member_info(settings,logger)

    update_avatar(settings)
    set_keybinds.update_keybinds(settings)

    while taskcancelled == False:
        try:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(listen(hostname,ws,settings,logger))
                tg.create_task(ping(hostname,ws))
                tg.create_task(chatbox_string(settings,chatbox_preview))
                tg.create_task(update_chatbox())
                tg.create_task(status_string(settings))
                tg.create_task(cancelcheck())
        except Exception as e:
            if taskcancelled == True:
                logger.emit("Closing...")
                chatbox_preview.emit("Not Connected")
                return
            elif settings["attempt_reconnect"] == True:
                logger.emit("Disconnected, attempting to reconnect. (5s)")
                await asyncio.sleep(5)
                continue
            elif settings["attempt_reconnect"] == False:
                logger.emit("Disconnected. Read exception for details:\n"+str(e))
                return

