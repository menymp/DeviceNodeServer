'''
simple core server task starter

menymp 
23 october 2023
'''
import subprocess
import sys
import json

sys.path.append('../ConfigsUtils')

def loadCoreProcesses(filePath = './processList.json'):
    # Opening JSON file
    f = open(filePath)
 
    # returns JSON object as 
    # a dictionary
    return json.load(f)["processes"]

def isProcessRunning(id, plist):
    state = False
    for process in plist:
        if process["id"] == id and process["state"] == "running":
            state = True
    return state

def checkDependences(process, plist):
    for dependent in process["depends"]:
        if not isProcessRunning(dependent, plist):
            return False
    return True

def tryRunnProcesses(plist):
    pRunning = 0
    for process in plist:
        if process["state"] == "stop" and checkDependences(process, plist):
            pRunning = pRunning + 1
            subprocess.run(process["path"], shell=False)
            #ToDo: set an ack flag from each process to the output to determie if
            #      the process started correctly
            process["state"] = "running"
        else:
            pRunning = pRunning + 1
    return pRunning

#The Idea behind this simple algoritm is to start the less dependent process first
#   for each iteration, new processes can be started once its dependences are meet
if __name__ == "__main__":
    plist = loadCoreProcesses()
    pCount = len(plist)
    while pCount != pRunning:
        pRunning = tryRunnProcesses(plist)
    pass