import socket
import os, sys
import json
from _thread import *
import pickle
import random
import time

ECHO_SERVER_VER = "V1.3"

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

with open("admins.txt") as f:
    admins = f.readlines()
admins = [x.strip() for x in admins]

print(admins)
with open("banlist.txt") as f:
    banned_ips = f.readlines()
banned_ips = [x.strip() for x in banned_ips]

print(banned_ips)

host = ""
port = 7777

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
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
    print("Connection from " + str(addr))
    banned = False
    for ip in banned_ips:
        if ip == addr[0]:
            message = {
            "data": "banned",
            "msgtype": "BANCONF",
            "channel": ""
            }
            conn.send(encode(message))
            banned = True
            conn.send(encode(message))
            conn.shutdown(socket.SHUT_RDWR)
            conn.close()
    if banned == False:
        message = {
            "data": "notbanned",
            "msgtype": "BANCONF",
            "channel": ""
            }
        conn.send(encode(message))
    

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
        
    else:
        message = {
        "data": "wrongver",
        "msgtype": "VERCONF",
        "channel": ""
        }
        conn.send(encode(message))
        correct_ver = False
        password_accepted = False
        
    

    if (password_accepted == True) and (correct_ver == True):
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
                        if user["addr"][0] in admins:
                            command = data["data"][(i+2):]
                            split_command = command.split()
                            print(split_command)
                            if split_command[0] == "/ban":
                                message = {
                                    "data": "reason_placeholder",
                                    "msgtype": "BAN",
                                    "channel": ""
                                    }
                                if cl["username"] == split_command[1]:
                                    target_client = cl
                                    ban = True
                            elif split_command[0] == "/kick":
                                for cl in clients:
                                    message = {
                                    "data": "reason_placeholder",
                                    "msgtype": "KICKED",
                                    "channel": ""
                                    }
                                    if cl["username"] == split_command[1]:
                                        target_client = cl
                                        kick = True
                    if (kick == True) or (ban == True):
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
                            with open("banlist.txt", "a") as f:
                                f.write(str(target_client["addr"][0]) + "\n")
                            banned_ips.append(target_client["addr"][0])
                                    
                    else: # Message
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
                conn.shutdown(socket.SHUT_RDWR)
                conn.close()
                clients.remove(user)
                break
    elif password_accepted == False:
        pass

while True:
    conn, addr = s.accept()
    start_new_thread(client_connection_thread, (conn, addr,))
    
    
