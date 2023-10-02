import os
import requests

url = 'http://your-php-endpoint.com/upload.php'
files = {}
for filename in os.listdir('.'):
    if filename.endswith('.py'):
        with open(filename, 'rb') as f:
            files['file[]'] = (filename, f.read())

r = requests.post(url, files=files)
print(r.text)