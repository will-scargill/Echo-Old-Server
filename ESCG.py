import pickle

config = []

print("ECHO SCG")
inp = input("Server name >>> ")
config.append(inp)
inp = input("Server MOTD >>> ")
config.append(inp)
inp = input("Channel name >>> ")
config.append(inp)
while True:
    inp = input("Channel name/q to finish >>> ")
    if inp == "q":
        break
    else:
        config.append(inp)
print(config)
outFile = open('config.txt', "wb")
pickle.dump(config, outFile)
outFile.close()
