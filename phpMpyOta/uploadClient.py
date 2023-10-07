import os
import requests
import sys

url = '#####/upythonota/versions/uploadUpdate.php'
files = []

data = {
    "projectName":""
}

def parseArgs():
    args = {}
    for arg in sys.argv:
        if arg =="uploadClient.py":
            continue
        tokens = arg.split("=")
        if len(tokens) != 2:
            continue
        if tokens[0] == "--name":
            args["name"] = tokens[1]
    return args


args = parseArgs()

data["projectName"] = args["name"]

#if not specified, python gets the current directory
for filename in os.listdir():
    print(filename)
    if filename.endswith('.py'):
        files.append((('files[]', ( filename,open(filename, 'rb'), 'file'))))
#print(files)
r = requests.post(url, data=data, files=files)
print(r.content)
print(r.text)