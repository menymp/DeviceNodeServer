import configparser
import os

class configsParser():
    def readConfigData(self, filePath = ""):
        if(filePath == ""):
            filePath = os.getcwd() + "\\configs.ini"
        config_obj = configparser.ConfigParser()
        config_obj.read(filePath)
        argsP = config_obj["connConfigs"]
        return [argsP["host"],argsP["dbname"],argsP["user"],argsP["pass"],argsP["broker"]]


#config = configparser.ConfigParser()
## Add the structure to the file we will create
#config.add_section('connConfigs')
#config.set('connConfigs', 'host', '')
#config.set('connConfigs', 'dbname', '')
#config.set('connConfigs', 'user', '')
#config.set('connConfigs', 'pass', '')
#config.set('connConfigs', 'broker', '')
#
## Write the new structure to the new file
#with open(r"C:\PythonTutorials\configfile.ini", 'w') as configfile:
#    config.write(configfile)
#
##Read config.ini file
#config_obj = configparser.ConfigParser()
#config_obj.read("C:\PythonTutorials\configfile.ini")
#dbparam = config_obj["connConfigs"]