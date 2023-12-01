'''
simple core server task starter

menymp 
23 october 2023
'''
import subprocess
import sys
import json
import signal
from threading import Event

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
            process["pipe"] = subprocess.Popen(process["path"], shell=True)
            print("subprocess '" + str(process["path"]) + "' started")
            #ToDo: set an ack flag from each process to the output to determie if
            #      the process started correctly
            process["state"] = "running"
        else:
            pRunning = pRunning + 1
    return pRunning

def stopProcesses(plist):
    for process in plist:
        process["pipe"].send_signal(signal.CTRL_BREAK_EVENT)
    pass

#The Idea behind this simple algoritm is to start the less dependent process first
#   for each iteration, new processes can be started once its dependences are meet
if __name__ == "__main__":
    plist = loadCoreProcesses()
    pCount = len(plist)
    pRunning = 0
    while pCount != pRunning:
        pRunning = tryRunnProcesses(plist)
    print("started '" + str(pRunning) + "' processes")

    eventStop = Event()
    def sigterm_handler(signum, frame):
        print("stop process")
        eventStop.set()
        stopProcesses(plist)
    signal.signal(signal.SIGINT, sigterm_handler)
    signal.signal(signal.SIGTERM, sigterm_handler)

    while not eventStop.is_set():
        pass
    pass