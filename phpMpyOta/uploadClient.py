import requests

url = 'http://..../uploadUpdate.php'
files = {'file': ('examplefile1.txt', open('examplefile1.txt', 'rb')),
         'file': ('examplefile2.txt', open('examplefile2.txt', 'rb'))}

r = requests.post(url, files=files)
print(r.text)