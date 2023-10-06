import os
import requests
import sys

url = '...../versions/uploadUpdate.php'
files = {}

def parseArgs():
    args = {}
    for arg in sys.argv:
        if arg =="uploadClient.py"
            continue
        tokens = arg.split("=")
        if len(tokens) != 2:
            continue
        if tokens[0] == "--name":
            args["name"] = tokens[1]
    return args


args = parseArgs()

files["name"] = args["name"]
files["files"] = []

#if not specified, python gets the current directory
for filename in os.listdir():
    if filename.endswith('.py'):
        with open(filename, 'rb') as f:
            files['files'].append({"name":filename, "data":f.read()})

r = requests.post(url, files=files)
print(r.text)