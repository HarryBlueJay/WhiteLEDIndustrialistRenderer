import os

files = os.listdir("./rendered/")
totalFiles = len(files)
string = ""
for index in range(totalFiles):
    string += "file './rendered/"+str(index)+".png'\n"
    string += "duration 0.033333\n"
file = open("files.txt","w")
print(string, file=file)
file.close()