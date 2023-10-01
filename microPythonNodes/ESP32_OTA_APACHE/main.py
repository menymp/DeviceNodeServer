'''

use examples from micropython-ota.py api

in the server apache is expected to have the following structure and use_version_prefix = false in the call
the library was altered to the following changes
version handles the current data as well as the list of files to download

the version file contents must have the following form
version and the expected file names to be downloaded with the version
{
   "version":"v1.0.0"
   "files":["main.py","boot.py","module.py"]
}

server-root/
|- <project_name>/
|  |- version
|  |- <version_subdir>
|     |- <filename1>
|     |- <filename2>
|     |- ...
|- <project_name>/
   |- version
   |- <version_subdir>
      |- <filename1>
      |- <filename2>
      |- ...

      
'''

import micropython_ota
import utime
import time
from example_module1 import module1_func
from example_module2 import module2_func
import network

ota_host = '<host>/upythonota/versions'
project_name = 'sample'
filenames = [] #not needed anymore
max_wait = 20

def wlanConnect(ssid, password):
    global max_wait
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        wlan.active(True)
        wlan.connect(ssid, password)
        print('Connecting to: %s' % ssid)
        timeout = time.ticks_ms()
        while not wlan.isconnected():
            time.sleep(0.15)
            if (time.ticks_diff (time.ticks_ms(), timeout) > 15000):
                break
        if wlan.isconnected():
            print('Successful connection to: %s' % ssid)
            print('IP: %s\nSUBNET: %s\nGATEWAY: %s\nDNS: %s' % wlan.ifconfig()[0:4])
        else:
            wlan.active(False)
            print('Failed to connect to: %s' % ssid)
    else:
        print('Connected\nIP: %s\nSUBNET: %s\nGATEWAY: %s\nDNS: %s' % wlan.ifconfig()[0:4])
    return wlan

wlanObj = wlanConnect('ssid','pwd')

micropython_ota.ota_update(ota_host, project_name, filenames, use_version_prefix=False, hard_reset_device=True, soft_reset_device=False, timeout=5)

while True:
    # do some other stuff
    print("new behavior")
    module1_func()
    module2_func()
    utime.sleep(10)
    micropython_ota.check_for_ota_update(ota_host, project_name, soft_reset_device=False, timeout=5)