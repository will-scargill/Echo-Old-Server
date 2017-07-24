import socket
import os, sys
import json
from _thread import *
import pickle
import random

try:
    inFile = open('config.txt', 'rb')
    config = pickle.load(inFile)
    inFile.close()
except FileNotFoundError:
    print("Error - Config file not found")

global channels
channels = []

servername = config[0]
print(servername)
password = config[1]
print(password)
motd = config[2]
print(motd)

for item in config:
    if (item == servername) or (item == motd) or (item==password):
        pass
    else:
        channels.append(item)

print(channels)

host = ""
port = 6666

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    #s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    s.bind((host, port))
except socket.error as e:
    print(e)

s.listen(6)
print("ECHO online")

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
    if password == "NOPASSWORD":
        password_required = False
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

    if password_accepted == True:
        message = {
        "data": motd,
        "msgtype": "MOTD",
        "channel": ""
        }
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
                    print("Yes")
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
                conn.shutdown(socket.SHUT_RDWR)
                conn.close()
                clients.remove(user)
                break
    elif password_accepted == False:
        pass

while True:
    conn, addr = s.accept()
    start_new_thread(client_connection_thread, (conn, addr,))
    
    
