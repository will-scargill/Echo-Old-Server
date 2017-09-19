from tkinter import *
from tkinter import messagebox
import os, sys
import socket
import threading
import sqlite3
import json
import time
import select
import errno
import operator

ECHO_CLIENT_VER = "V1.4.2" # DO NOT CHANGE

#========================================
# SQLite Setup

conn = sqlite3.connect("database.db", check_same_thread=False)
c = conn.cursor()

tables = [
    {
        "name": "servers",
        "columns": "name TEXT, ip TEXT, port NUMBER"
    },
]

for table in tables:
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", [table["name"]])
    data = c.fetchall()

    if len(data) <= 0:  # If table doesn't exist
        c.execute("CREATE TABLE " +
                  
                  table["name"] + " (" + table["columns"] + ")")
        c.execute("INSERT INTO servers (name, ip, port) VALUES ('ECHO Official Server', '144.172.89.154', 6666)")
        conn.commit()


#========================================

#This has to be above so functions can use the variables
root = Tk()
root.title("ECHO")
root.geometry("600x300")
root.grid_columnconfigure(0,weight=1)
root.grid_rowconfigure(0,weight=1)

frame_mainmenu = Frame(root)
frame_mainmenu.grid(row=0, column=0)

#========================================
# Main Server Connection
def connect():
    #========================================
    #These functions will make this a hell of a lot easier
    def encode(data):
        data = json.dumps(data) #Json dump message
        data = data.encode('utf-8') #Encode message in utf-8
        return(data) 
    def decode(data):
        data = data.decode('utf-8') #Decode utf-8 data
        data = json.loads(data) #Load from json
        return(data)
    #========================================
    server_name = element_listbox_servers.get(ACTIVE)
    username = element_entry_username.get()
    
    
    frame_mainmenu.grid_forget()
    element_label_loading = Label(root, text="Trying to connect...")
    element_label_loading.grid(row=0, column=0)
    root.update()

    #========================================
    #Connection Setup
    try:
        c.execute("SELECT * FROM servers WHERE name=?", [server_name])
        server_data = c.fetchall()
        ip = server_data[0][1]
        port = server_data[0][2]
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
        element_label_loading.grid_forget()
        var_check_continue = 1

        global selected_channel
        selected_channel = ""
        
    #========================================

    except ConnectionRefusedError:
        def end_error_screen__connrefused():
            element_label_connerror.grid_forget()
            element_label_loading.grid_forget()
            element_button_enderror.grid_forget()
            frame_mainmenu.grid(row=0, column=0)
        element_label_connerror = Label(root, text="Error - Connection failed")
        element_label_connerror.grid(row=0, column=0)
        element_button_enderror = Button(root, text="Ok", command=end_error_screen__connrefused, height=2, width=4)
        element_button_enderror.grid(row=1, column=0)
        var_check_continue = 0
                                     
    except OSError as e:
        def end_error_screen__oserror():
            element_label_connerror.grid_forget()
            element_label_loading.grid_forget()
            element_button_enderror.grid_forget()
            frame_mainmenu.grid(row=0, column=0)
        element_label_connerror = Label(root, text="Error - Network unreachable")
        element_label_connerror.grid(row=0, column=0)
        element_button_enderror = Button(root, text="Ok", command=end_error_screen__oserror, height=2, width=4)
        element_button_enderror.grid(row=1, column=0)
        var_check_continue = 0
    except TypeError:
        if server_name == "debug_bypass_connection":
            var_check_continue = 1
            element_label_loading.grid_forget()
        else:
            def end_error_screen__missingdetailserror():
                element_label_connerror.grid_forget()
                element_label_loading.grid_forget()
                element_button_enderror.grid_forget()
                frame_mainmenu.grid(row=0, column=0)
            element_label_connerror = Label(root, text="Error - Check server settings for IP and Port")
            element_label_connerror.grid(row=0, column=0)
            element_button_enderror = Button(root, text="Ok", command=end_error_screen__oserror, height=2, width=4)
            element_button_enderror.grid(row=1, column=0)
            var_check_continue = 0
        
        
        


    
    if var_check_continue == 1:
        def main_connection_function():
            global password_required
            if password_required == True:
                password = entry_password.get()
                message = {
                        "data": password,
                        "msgtype": "PASSWORD",
                        "channel": ""
                        }
                s.send(encode(message))

                data = s.recv(1024)
                data = decode(data)
                if data["data"] == "rightpass":
                    password_required = False
                elif data["data"] == "wrongpass":
                    password_required = True
            if password_required == False:
                #MAIN PROGRAM START
                data = s.recv(1024)
                data = decode(data)
                server_motd = data["data"]

                message = {
                "data": username,
                "msgtype": "USERNAME",
                "channel": ""
                }

                s.send(encode(message))
                

                data = s.recv(1024)
                data = decode(data)

                

                server_channels = data["data"]
                
                
                root.geometry("600x450")

                def retrieve_server_infomation():
                    pass
                
                frame_mainchat = Frame(root)
                frame_mainchat.grid(row=0, column=0)
                
                #========================================
                #Menu Commands

                def view_all_users():
                    
                    global server_client_lists
                    popup_users = Tk()
                    popup_users.title("ECHO - User List")
                    message = {
                        "data": "",
                        "msgtype": "USERLIST",
                        "channel": ""
                        }
                    s.send(encode(message))
                    time.sleep(1)
                    user_labels = {}
                    i = 0
                    for cl in server_client_list:
                        i += 1
                        user_labels[cl] = Label(popup_users, text=cl)
                        user_labels[cl].grid(row=i, column=0)
                    

                def disconnect():
                    try:
                        frame_passreq.grid_forget()
                    except NameError:
                        pass
                    s.shutdown(socket.SHUT_RDWR)
                    s.close()
                    root.geometry("600x300")
                    frame_mainchat.grid_forget()
                    frame_mainmenu.grid(row=0, column=0)
                    root.unbind("<Return>")
                    element_listbox_channelselect.unbind("<<ListboxSelect>>")
                    blankmenu = Menu(root)
                    root.config(menu=blankmenu)
                    root.title("ECHO")

                    
                    
                
                

                #========================================
                
                #========================================
                #Topbar Menu

                element_menu = Menu(root)

                root.geometry("900x500")

                element_menu.add_command(label="View all users", command=view_all_users)
                element_menu.add_command(label="Disconnect", command=disconnect)

                root.config(menu=element_menu)
                
                #========================================

                #========================================
                #Channel Selection and Client Output

                
                def join_channel(args):
                    global selected_channel
                    old_channel = selected_channel
                    try:
                        selected_channel = element_listbox_channelselect.get(element_listbox_channelselect.curselection())
                    except TclError:
                        pass
                    if old_channel == selected_channel:
                        pass
                    else:
                        element_listbox_chatdisplay.delete(0, END)
                        for i in range(element_listbox_chatdisplay.cget('height')-1):
                            element_listbox_chatdisplay.insert(0, '')
                    message = {
                        "data": selected_channel,
                        "msgtype": "CHANNELJOIN",
                        "channel": ""
                        }
                    s.send(encode(message))
                    
                        
               

                element_listbox_channelselect = Listbox(frame_mainchat, height = 20, width=25)
                element_listbox_channelselect.grid(row=0, column=0)

                element_listbox_channelclients = Listbox(frame_mainchat, height = 20, width=25)
                element_listbox_channelclients.grid(row=0, column=2)

                for channel in server_channels:
                    element_listbox_channelselect.insert(END, channel)

                

                element_listbox_channelselect.bind("<<ListboxSelect>>", join_channel) 
                #========================================
                
                element_listbox_chatdisplay = Listbox(frame_mainchat, height=20, width=100)
                element_listbox_chatdisplay.grid(row=0, column=1)

                for i in range(element_listbox_chatdisplay.cget('height')-1):
                    element_listbox_chatdisplay.insert(0, '')

                element_listbox_chatdisplay.insert(0, server_motd)

                def submit_message(args):
                    global username
                    user_input = element_entry_chatinput.get()
                    if selected_channel == "":
                        element_listbox_chatdisplay.insert(END, "[{}] ".format(username) + str(user_input) )
                        element_listbox_chatdisplay.see(END)
                        element_entry_chatinput.delete('0', END)
                    else:
                        message = {
                            "data": "[{}] ".format(username) + str(user_input),
                            "msgtype": "MSG-SB",
                            "channel": selected_channel
                            }
                        s.send(encode(message))
                        element_entry_chatinput.delete('0', END)

                element_entry_chatinput = Entry(frame_mainchat, width=100)
                element_entry_chatinput.grid(row=1, column=1)

                root.bind("<Return>", submit_message)

                def recv_data():
                    global selected_channel
                    s.setblocking(0)
                    while True:
                        try:
                            r, _, _ = select.select([s], [], [])
                            if r:
                                data = s.recv(2048)
                                data = decode(data)
                                if data["msgtype"] == "MSG":
                                    pass
                                elif data["msgtype"] == "CHANNELCLIENTS":
                                    channel_clients = data["data"]

                                    element_listbox_channelclients.delete(0, END)
                                    element_listbox_channelclients.delete(1, END)
                                    
                                    for client in channel_clients:
                                        element_listbox_channelclients.insert(END, client)
                                elif data["msgtype"] == "CLIENTDISCONN":
                                    if data["channel"] != selected_channel:
                                        pass
                                    else:
                                        tempclientlist = element_listbox_channelclients.get(0, END)
                                        
                                        for i, j in enumerate(tempclientlist):
                                            if j == data["data"]:
                                                element_listbox_channelclients.delete(i)
                                                break
                                        
                                        
                                elif data["msgtype"] == "USERTAKEN":
                                    global username
                                    username = data["data"]
                                    root.title("ECHO - " + username)
                                    
                                elif data["msgtype"] == "MSG-CB":
                                    element_listbox_chatdisplay.insert(END, data["data"])
                                    element_listbox_chatdisplay.see(END)
                                    
                                elif data["msgtype"] == "USERLIST":
                                    global server_client_list
                                    server_client_list = data["data"]
                                elif data["msgtype"] == "KICKED":
                                    frame_mainchat.grid_forget()
                                    try:
                                        frame_passreq.grid_forget()
                                    except NameError:
                                        pass
                                    def end_error_screen__wrongpasserror():
                                        element_label_kicked.grid_forget()
                                        #####element_label_loading.grid_forget()
                                        element_button_enderror.grid_forget()
                                        frame_mainmenu.grid(row=0, column=0)
                                    element_label_kicked = Label(root, text="You have been kicked from the server - Reason: " + data["data"])
                                    element_label_kicked.grid(row=0, column=0)
                                    element_button_enderror = Button(root, text="Ok", command=end_error_screen__wrongpasserror, height=2, width=4)
                                    element_button_enderror.grid(row=1, column=0)
                                    root.geometry("600x300")
                                    break
                                elif data["msgtype"] == "BAN":
                                    frame_mainchat.grid_forget()
                                    try:
                                        frame_passreq.grid_forget()
                                    except NameError:
                                        pass
                                    def end_error_screen__wrongpasserror():
                                        element_label_kicked.grid_forget()
                                        #####element_label_loading.grid_forget()
                                        element_button_enderror.grid_forget()
                                        frame_mainmenu.grid(row=0, column=0)
                                    element_label_kicked = Label(root, text="You have been banned from the server - Reason: " + data["data"])
                                    element_label_kicked.grid(row=0, column=0)
                                    element_button_enderror = Button(root, text="Ok", command=end_error_screen__wrongpasserror, height=2, width=4)
                                    element_button_enderror.grid(row=1, column=0)
                                    root.geometry("600x300")
                                    break
                            else:
                                pass
                        except socket.error as e:
                            if e.args[0] == errno.EWOULDBLOCK: 
                                time.sleep(0.25)
                            else:
                                print("Debug Printout ==Start==")
                                print(e)
                                print("Debug Printout ==End==")
                                break

                 
                thread_recv_data = threading.Thread(target=recv_data)
                thread_recv_data.start()
                    
    
                    
            elif password_required == True:
                entry_password.grid_forget()
                button_submit_password.grid_forget()
                label_enter_password.grid_forget()
                frame_passreq.grid_forget()
                def end_error_screen__wrongpasserror():
                    element_label_connerror.grid_forget()
                    element_label_loading.grid_forget()
                    element_button_enderror.grid_forget()
                    frame_mainmenu.grid(row=0, column=0)
                element_label_connerror = Label(root, text="Error - Password Incorrect")
                element_label_connerror.grid(row=0, column=0)
                element_button_enderror = Button(root, text="Ok", command=end_error_screen__wrongpasserror, height=2, width=4)
                element_button_enderror.grid(row=1, column=0)

        data = s.recv(1024)
        data = decode(data)
        if data["data"][0] == "banned":
            def end_error_screen__oserror():
                element_label_connerror.grid_forget()
                element_label_loading.grid_forget()
                element_button_enderror.grid_forget()
                frame_mainmenu.grid(row=0, column=0)
            element_label_connerror = Label(root, text="Error - You are banned from this server - Reason: " + str(data["data"][1]))
            element_label_connerror.grid(row=0, column=0)
            element_button_enderror = Button(root, text="Ok", command=end_error_screen__oserror, height=2, width=4)
            element_button_enderror.grid(row=1, column=0)
        elif data["data"][0] == "notbanned":
            message = {
                "data": ECHO_CLIENT_VER,
                "msgtype": "CLIENTVER",
                "channel": ""
                }
            s.send(encode(message))
            data = s.recv(1024)
            data = decode(data)
            if data["data"] == "rightver":
                data = s.recv(1024)
                data = decode(data)
                global password_required
                if data["msgtype"] == "PASSREQ":
                    frame_passreq = Frame(root)
                    frame_passreq.grid(row=0, column=0)
                    entry_password = Entry(frame_passreq)
                    entry_password.configure(show="*")
                    entry_password.grid(row=1, column=0)
                    entry_password.focus()
                    
                    button_submit_password = Button(frame_passreq, text="Submit", command=main_connection_function, height=2, width=10)
                    button_submit_password.grid(row=2, column=0)

                    label_enter_password = Label(frame_passreq, text="Enter Password")
                    label_enter_password.grid(row=0, column=0)
                    global password_required
                    global password_accepted
                    password_required = True
                else:
                    password_required = False
                    main_connection_function()
            else:
                def end_error_screen__oserror():
                    element_label_connerror.grid_forget()
                    element_label_loading.grid_forget()
                    element_button_enderror.grid_forget()
                    frame_mainmenu.grid(row=0, column=0)
                element_label_connerror = Label(root, text="Error - Wrong Version")
                element_label_connerror.grid(row=0, column=0)
                element_button_enderror = Button(root, text="Ok", command=end_error_screen__oserror, height=2, width=4)
                element_button_enderror.grid(row=1, column=0)
        
        

        
        
    elif var_check_continue == 0:
        pass
    else:
        messagebox.showinfo("Fatal Error", "An unexpected error occured")
        os._exit(0)
        
    
    

#========================================


#========================================
# Menu Section

def settings_menu():
    def add_server():
        name = element_entry_servername.get()
        ip = element_entry_ip.get()
        port = element_entry_port.get()
        c.execute("INSERT INTO servers (name, ip, port) VALUES (?, ?, ?)", [name, ip, port])
        conn.commit()
        element_listbox_servers.insert(END, name)
        element_listbox_settings_servers.insert(END, name)
        
    def del_server():
        name = element_listbox_settings_servers.get(ACTIVE)
        result = messagebox.askquestion("Delete", "Are you sure?", icon='warning')
        if result == "yes":
            c.execute("DELETE FROM servers WHERE name=?", [name])
            conn.commit()
            element_listbox_servers.delete(ACTIVE)
            element_listbox_settings_servers.delete(ACTIVE)
            for server in variable_servers:
                if server[0] == name:
                    variable_servers.remove(server)
                else:
                    pass
        else:
            pass
        
    def update_server():
        name = element_listbox_settings_servers.get(ACTIVE)
        result = messagebox.askquestion("Update", "Are you sure?", icon='warning')
        if result == "yes":
            c.execute("UPDATE servers SET name=?, ip=?, port=? WHERE name=?", [element_entry_servername.get(), element_entry_ip.get(), element_entry_port.get(), name])
            conn.commit()
        else:
            pass
        
    def save_settings():
        root.geometry("600x300")
        frame_mainmenu.grid(row=0, column=0)
        frame_settingsmenu.grid_forget()
        element_listbox_settings_servers.unbind("<<ListboxSelect>>") 
    
    root.geometry("600x300")
    frame_settingsmenu = Frame(root)
    frame_settingsmenu.grid(row=0, column=0)
    for i in range(4):
        frame_settingsmenu.grid_columnconfigure(i,weight=1)
        frame_settingsmenu.grid_rowconfigure(i,weight=1)
    frame_mainmenu.grid_forget()
    element_listbox_settings_servers = Listbox(frame_settingsmenu, height=18, width=50)
    for server in variable_servers:
        element_listbox_settings_servers.insert(END, server[0])
    element_listbox_settings_servers.grid(row=0, column=0, rowspan=5)
    
    element_entry_servername = Entry(frame_settingsmenu)
    element_entry_servername.grid(row=0, column=2, pady=0)
    element_label_servername = Label(frame_settingsmenu, text="Server Name: ")
    element_label_servername.grid(row=0, column=1)

    element_entry_ip = Entry(frame_settingsmenu)
    element_entry_ip.grid(row=1, column=2, pady=0)
    element_label_ip = Label(frame_settingsmenu, text="Server IP: ")
    element_label_ip.grid(row=1, column=1)
    
    element_entry_port = Entry(frame_settingsmenu)
    element_entry_port.grid(row=2, column=2, pady=0)
    element_label_port = Label(frame_settingsmenu, text="Port: ")
    element_label_port.grid(row=2, column=1)

    element_button_add_server = Button(frame_settingsmenu, text="Add Server", command=add_server, height=2, width=10)
    element_button_add_server.grid(row=3, column=2)

    element_button_delete_server = Button(frame_settingsmenu, text="Delete Server", command=del_server, height=2, width=12)
    element_button_delete_server.grid(row=3, column=1)

    element_button_exit_settings = Button(frame_settingsmenu, text="Exit", command=save_settings, height=2, width=10)
    element_button_exit_settings.grid(row=4, column=2)

    element_button_update_server = Button(frame_settingsmenu, text="Update Server", command=update_server, height=2, width=12)
    element_button_update_server.grid(row=4, column=1)

    def insert_server_infomation(args):
        selected_server_name = element_listbox_settings_servers.get(element_listbox_settings_servers.curselection())
        c.execute("SELECT * FROM servers WHERE name=?", [selected_server_name])
        selected_server_data = c.fetchall()
        element_entry_servername.delete(0, END)
        element_entry_ip.delete(0, END)
        element_entry_port.delete(0, END)
        element_entry_servername.insert(0, selected_server_data[0][0])
        element_entry_ip.insert(0, selected_server_data[0][1])
        element_entry_port.insert(0, selected_server_data[0][2])
                                        
        
        
        

    element_listbox_settings_servers.bind("<<ListboxSelect>>", insert_server_infomation) 

    

for i in range(4):
    frame_mainmenu.grid_columnconfigure(i,weight=1)
    frame_mainmenu.grid_rowconfigure(i,weight=1)

try:
    variable_photo_cogicon = PhotoImage(file="icon.gif")

    element_button_settings = Button(frame_mainmenu, command=settings_menu)
    element_button_settings.grid(row=0, column=4, sticky=(NE))
    element_button_settings.config(image=variable_photo_cogicon)
except:
    element_button_settings = Button(frame_mainmenu, text="S", command=settings_menu, bg=white)
    element_button_settings.grid(row=0, column=4, sticky=(NE))
    


c.execute("SELECT * FROM servers")
variable_servers = c.fetchall()

element_listbox_servers = Listbox(frame_mainmenu, height=18, width=50)
for server in variable_servers:
    element_listbox_servers.insert(END, server[0])
element_listbox_servers.grid(row=0, column=0, rowspan=3)

element_button_connect = Button(frame_mainmenu, text="Connect", command=connect, height=2, width=10)
element_button_connect.grid(row=2, column=1)

element_entry_username = Entry(frame_mainmenu)
element_entry_username.grid(row=1, column=1)
element_entry_username.insert(0, "Username")

def user_entry_del_text(args):
    element_entry_username.delete(0, END)

element_entry_username.bind("<FocusIn>", user_entry_del_text)

element_label_echo = Label(frame_mainmenu, text="ECHO")
element_label_echo.grid(row=0, column=1)


root.mainloop()

#========================================
