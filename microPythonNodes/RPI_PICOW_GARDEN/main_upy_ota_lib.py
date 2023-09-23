'''

use examples from micropython-ota.py api

in the server apache is expected to have the following structure and use_version_prefix = false in the call

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

ota_host = 'http://192.168.2.100'
project_name = 'sample'

while True:
    # do some other stuff
    utime.sleep(10)
    micropython_ota.check_for_ota_update(ota_host, project_name, soft_reset_device=False, timeout=5)