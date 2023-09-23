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

ota_host = 'http://192.168.2.100'
project_name = 'sample'

while True:
    # do some other stuff
    utime.sleep(10)
    micropython_ota.check_for_ota_update(ota_host, project_name, soft_reset_device=False, timeout=5)