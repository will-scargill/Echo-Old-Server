import socket
import os, sys
import json
from _thread import *
import pickle
import random
import time
import sqlite3
import datetime

ECHO_SERVER_VER = "V1.4.2" # DO NOT CHANGE

#========================================
# SQLite Setup

sqlite3_conn = sqlite3.connect("database.db", check_same_thread=False)
c = sqlite3_conn.cursor()

tables = [
    {
        "name": "banned_ips",
        "columns": "ip TEXT, date_banned TEXT, reason TEXT"
    },
    {
        "name": "admin_ips",
        "columns": "ip TEXT"
    },
    {
        "name": "chatlogs",
        "columns": "ip TEXT, username TEXT, channel TEXT, date TEXT, message TEXT"
    },
    {
        "name": "commandlogs",
        "columns": "ip TEXT, username TEXT, channel TEXT, date TEXT, command TEXT, reason TEXT"
    },
    {
        "name": "pmlogs",
        "columns": "ip TEXT, username TEXT, channel TEXT, date TEXT, message TEXT"
    },
    {
        "name": "config",
        "columns": "data TEXT, type TEXT"
    },
]

for table in tables:
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", [table["name"]])
    data = c.fetchall()

    if len(data) <= 0:  # If table doesn't exist
        c.execute("CREATE TABLE " +
                  
                  table["name"] + " (" + table["columns"] + ")")



#========================================

global channels
channels = []

#Setup to check if the Config is not set up correctly
servername = ""
password = ""
chatlog_settings = ""
motd = ""


c.execute("SELECT * FROM config")
config = c.fetchall()

for item in config:
    if item[1] == "servername":
        servername = item[0]
    elif item[1] == "password":
        password = item[0]
    elif item[1] == "chatlogsetting":
        chatlog_settings = item[0]
    elif item[1] == "motd":
        motd = item[0]
    else:
        channels.append(item[0])

admins = []
c.execute("SELECT * FROM admin_ips")
data = c.fetchall()
for item in data:
    admins.append(item[0])

#################### Change this
host = ""          # 
port = 6666        # 
#################### Change this

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind((host, port))
except socket.error as e:
    print(e)

s.listen(20)
print("All ECHO data loaded")

global clients
clients = []

def client_connection_thread(conn, addr):
    #========================================
    #These functions will make this a hell of a lot easier
    def encode(data):
        data = json.dumps(data)
        data = data.encode('utf-8')
        return(data)
    def decode(data):
        data = data.decode('utf-8')
        data = json.loads(data)
        return(data)
    #========================================
    
    banned = False
    c.execute("SELECT * FROM banned_ips")
    banned_ips = c.fetchall()
    for ip in banned_ips:
        if ip[0] == addr[0]:
            print("Banned ip attempted to connect " + str(addr))
            data = []
            data.append("banned")
            data.append(ip[1])
            message = {
            "data": data,
            "msgtype": "BANCONF",
            "channel": ""
            }
            conn.send(encode(message))
            banned = True
            conn.send(encode(message))
            conn.shutdown(socket.SHUT_RDWR)
            conn.close()
    if banned == False:
        print("Connection from " + str(addr))
        data = []
        data.append("notbanned")
        message = {
            "data": data,
            "msgtype": "BANCONF",
            "channel": ""
            }
        conn.send(encode(message))
        user_banned = False
    

        data = conn.recv(1024)
        data = decode(data)
    
    if data["data"] == ECHO_SERVER_VER:
        message = {
        "data": "rightver",
        "msgtype": "VERCONF",
        "channel": ""
        }
        conn.send(encode(message))
        correct_ver = True

        if password == "NOPASSWORD":
            password_required = False
            password_accepted = True
            message = {
            "data": "",
            "msgtype": "NOPASS",
            "channel": ""
            }
            conn.send(encode(message))
        else:
            password_required = True
            message = {
            "data": "",
            "msgtype": "PASSREQ",
            "channel": ""
            }
            conn.send(encode(message))

            data = conn.recv(1024)
            if data == b"":
                print("Client " + str(addr) + " disconnected")
                password_accepted = False
            else:
                data = decode(data)
                
                if data["data"] == password:
                    message = {
                    "data": "rightpass",
                    "msgtype": "PASSCONF",
                    "channel": ""
                    }
                    conn.send(encode(message))
                    password_accepted = True
                else:
                    message = { 
                    "data": "wrongpass",
                    "msgtype": "PASSCONF",
                    "channel": ""
                    }
                    conn.send(encode(message))
                    conn.shutdown(socket.SHUT_RDWR)
                    conn.close()
                    password_accepted = False

    elif data["data"] == "userbanned":
        user_banned = True
        correct_ver = False
        password_accepted = False
    else:
        message = {
        "data": "wrongver",
        "msgtype": "VERCONF",
        "channel": ""
        }
        conn.send(encode(message))
        correct_ver = False
        password_accepted = False
        
    

    if (password_accepted == True) and (correct_ver == True) and (user_banned == False):
        if chatlog_settings == "LOGS":
            message = {
            "data": motd + " \n    |Notice: This server stores records of all chat messages|",
            "msgtype": "MOTD",
            "channel": ""
            }
        else:
            message = {
            "data": motd,
            "msgtype": "MOTD",
            "channel": ""
            }
        time.sleep(0.5)
        conn.send(encode(message))
                    
		
        data = conn.recv(1024)
        data = decode(data)
        
        

        user = {
            "conn": conn,
            "addr": addr,
            "username": data["data"],
            "channel": ""
            }
        
        for client in clients:
            if user["username"] == client["username"]:
                user = {
                    "conn": conn,
                    "addr": addr,
                    "username": (str(data["data"]) + str(random.randint(1,10))),
                    "channel": ""
                    }
                
            else:
                user = {
                    "conn": conn,
                    "addr": addr,
                    "username": data["data"],
                    "channel": ""
                    }

        clients.append(user)
        
        message = {
            "data": channels,
            "msgtype": "CHANNELS",
            "channel": ""
            }
        conn.send(encode(message))

        message = {
                    "data": user["username"],
                    "msgtype": "USERTAKEN",
                    "channel": ""
                    }
        conn.send(encode(message))

        while True:
            try:
                data = conn.recv(1024)
                data = decode(data)
                if data["msgtype"] == "MSG-SB":
                    i = data["data"].index("]")
                    kick = False
                    ban = False
                    if data["data"][i + 2] == "/": # Command
                        command = data["data"][(i+2):]
                        split_command = command.split()
                        if split_command[0] == "/pm":
                            if chatlog_settings == "LOGS":
                                pm_message = " ".join(split_command[2:])
                                date = datetime.datetime.now()
                                c.execute("INSERT INTO pmlogs (ip, username, channel, date, message) VALUES (?, ?, ?, ?, ?)", [str(user["addr"]), user["username"], user["channel"], date, pm_message])
                                sqlite3_conn.commit()
                            else:
                                pass
                            for cl in clients:
                                if cl["username"] == split_command[1]:
                                    target_client = cl
                                    pm_message = " ".join(split_command[2:])
                                    pm_sendee_data = "{PM from " + split_command[1] + "} " + pm_message
                                    pm_sender_data = "{PM to " + split_command[1] + "} " + pm_message
                                    message = {
                                        "data": pm_sendee_data,
                                        "msgtype": "MSG-CB",
                                        "channel": ""
                                        }
                                    target_client["conn"].send(encode(message))
                                    message = {
                                        "data": pm_sender_data,
                                        "msgtype": "MSG-CB",
                                        "channel": ""
                                        }
                                    conn.send(encode(message))
                        else:
                            if user["addr"][0] in admins:
                                if split_command[0] == "/ban":
                                    reason = " ".join(split_command[2:])
                                    message = {
                                        "data": reason,
                                        "msgtype": "BAN",
                                        "channel": ""
                                        }
                                    if cl["username"] == split_command[1]:
                                        target_client = cl
                                        ban = True
                                elif split_command[0] == "/kick":
                                    for cl in clients:
                                        reason = " ".join(split_command[2:])
                                        message = {
                                        "data": reason,
                                        "msgtype": "KICKED",
                                        "channel": ""
                                        }
                                        if cl["username"] == split_command[1]:
                                            target_client = cl
                                            kick = True
                                elif split_command[0] == "/whois":
                                    date = datetime.datetime.now()
                                    c.execute("INSERT INTO commandlogs (ip, username, channel, date, command) VALUES (?, ?, ?, ?, ?)", [str(user["addr"]), user["username"], user["channel"], date, data["data"]])
                                    sqlite3_conn.commit()
                                    for cl in clients:
                                        if cl["username"] == split_command[1]:
                                            target_addr = cl["addr"]
                                    message = {
                                        "data": target_addr,
                                        "msgtype": "MSG-CB",
                                        "channel": ""
                                        }
                                else:
                                    message = {
                                        "data": "This is not a command",
                                        "msgtype": "MSG-CB",
                                        "channel": ""
                                        }
                                user["conn"].send(encode(message))
                                    
                            else:
                                message = {
                                        "data": "You are not an admin",
                                        "msgtype": "MSG-CB",
                                        "channel": ""
                                        }
                                user["conn"].send(encode(message))
                    if (kick == True) or (ban == True):
                        date = datetime.datetime.now()
                        reason = " ".join(split_command[2:])
                        c.execute("INSERT INTO commandlogs (ip, username, channel, date, command, reason) VALUES (?, ?, ?, ?, ?, ?)", [str(user["addr"]), user["username"], user["channel"], date, data["data"], reason])
                        sqlite3_conn.commit()
                        target_client["conn"].send(encode(message))
                        target_client["conn"].shutdown(socket.SHUT_RDWR)
                        target_client["conn"].close()
                        clients.remove(target_client)
                        for cl in clients:
                            if cl["channel"] == target_client["channel"]:
                                message = {
                                "data": target_client["username"],
                                "msgtype": "CLIENTDISCONN",
                                "channel": target_client["channel"]
                                }
                                cl["conn"].send(encode(message))
                        if ban == True:
                            date = datetime.datetime.now()
                            reason = " ".join(split_command[2:])
                            c.execute("INSERT INTO banned_ips (ip, date_banned, reason) VALUES (?, ?, ?)", [str(target_client["addr"][0]), date, reason])
                            sqlite3_conn.commit()
                            #with open("banlist.txt", "a") as f:
                                #f.write(str(target_client["addr"][0]) + "\n")
                            #banned_ips.append(target_client["addr"][0])
                                    
                    elif data["data"][i + 2] != "/": # Message
                        if chatlog_settings == "LOGS":
                            date = datetime.datetime.now()
                            c.execute("INSERT INTO chatlogs (ip, username, channel, date, message) VALUES (?, ?, ?, ?, ?)", [str(user["addr"]), user["username"], user["channel"], date, data["data"]])
                            sqlite3_conn.commit()
                        else:
                            pass
                        for cl in clients:
                            if cl["channel"] == data["channel"]:
                                message = {
                                "data": data["data"],
                                "msgtype": "MSG-CB",
                                "channel": data["channel"]
                                }
                                cl["conn"].send(encode(message))
                
                        
                elif data["msgtype"] == "CHANNELJOIN":
                    old_channel = user["channel"]
                    user["channel"] = data["data"]
                    channel_clients_list = []
                    for cl in clients:
                        if cl["channel"] == user["channel"]:
                            channel_clients_list.append(cl["username"])
                        else:
                            pass
                    message = {
                        "data": channel_clients_list,
                        "msgtype": "CHANNELCLIENTS",
                        "channel": ""
                        }
                    for cl in clients:
                        if cl["channel"] == user["channel"]:
                            message = {
                                "data": channel_clients_list,
                                "msgtype": "CHANNELCLIENTS",
                                "channel": ""
                                }
                            cl["conn"].send(encode(message))
                        elif cl["channel"] != user["channel"]:
                            message = {
                                "data": user["username"],
                                "msgtype": "CLIENTDISCONN",
                                "channel": old_channel
                                }
                            cl["conn"].send(encode(message))
                        else:
                            pass
                elif data["msgtype"] == "USERLIST":
                    server_clients_list = []
                    for cl in clients:
                        server_clients_list.append(cl["username"])
                    message = {
                        "data": server_clients_list,
                        "msgtype": "USERLIST",
                        "channel": ""
                        }
                    conn.send(encode(message))
            except (ValueError, ConnectionResetError) as e:
                print(user["channel"])
                for cl in clients:
                    print(cl["channel"])
                    if cl["channel"] == user["channel"]:
                        #print("Check")
                        message = {
                                "data": user["username"],
                                "msgtype": "CLIENTDISCONN",
                                "channel": user["channel"]
                                }
                        cl["conn"].send(encode(message))
                conn.shutdown(socket.SHUT_RDWR)
                conn.close()
                clients.remove(user)
                
                print("Client " + str(addr) + " disconnected")
                break
    elif password_accepted == False:
        pass
    elif user_banned == True:
        print("Banned user attempted to connect")

if (servername=="") or (password=="") or (chatlog_settings=="") or (channels==[]):
    print("!!!WARNING!!! Some or all of the config is not setup. Please select option 2 before starting ECHO")
while True:
    print("""
ECHO Server Administration Menu
1 - Start ECHO
2 - Edit Server Config
3 - Add Admins
""")

    choice = input(">>> ")
    if choice == "1":
        print("Started ECHO")
        while True:
            conn, addr = s.accept()
            start_new_thread(client_connection_thread, (conn, addr,))
    elif choice == "2":
        ##############################################################
        ### NEED TO ADD CODE HERE TO DELETE CONFIG BEFORE CHANGING ###
        ##############################################################
        inp = input("Input Server Name >>> ")
        c.execute("INSERT INTO config (data, type) VALUES (?, ?)", [inp, "servername"])
        sqlite3_conn.commit()

        inp = input("Input Server MOTD >> ")
        c.execute("INSERT INTO config (data, type) VALUES (?, ?)", [inp, "motd"])
        sqlite3_conn.commit()

        inp = input("Input Server Password/q for no password >>> ")
        if inp == "q":
            c.execute("INSERT INTO config (data, type) VALUES (?, ?)", ["NOPASSWORD", "password"])
            sqlite3_conn.commit()
        else:
            c.execute("INSERT INTO config (data, type) VALUES (?, ?)", [inp, "password"])
            sqlite3_conn.commit()
        while True:
            inp = input("Store Server Chat Logs? y/n >>> ")
            if inp == "y":
                c.execute("INSERT INTO config (data, type) VALUES (?, ?)", ["LOGS", "chatlogsetting"])
                sqlite3_conn.commit()
                break
            elif inp == "n":
                c.execute("INSERT INTO config (data, type) VALUES (?, ?)", ["NOLOGS", "chatlogsetting"])
                sqlite3_conn.commit()
                break
            else:
                pass
        while True:
            inp = input("Channel Name/q to finish >>> ")
            if inp == "q":
                break
            else:
                c.execute("INSERT INTO config (data, type) VALUES (?, ?)", [inp, "channel"])
                sqlite3_conn.commit()
        c.execute("SELECT * FROM config")
        config = c.fetchall()

        for item in config:
            if item[1] == "servername":
                servername = item[0]
            elif item[1] == "password":
                password = item[0]
            elif item[1] == "chatlogsetting":
                chatlog_settings = item[0]
            elif item[1] == "motd":
                motd = item[0]
            else:
                channels.append(item[0])
    elif choice == "3":
        inp = input("Input Admin IP >>> ")
        c.execute("INSERT INTO admin_ips (ip) VALUES (?)", [inp])
        sqlite3_conn.commit()
        admins.append(inp)
       
    
    
