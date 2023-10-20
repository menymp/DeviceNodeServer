'''
# Apr 2023 - reconverted form yapsc project, better to make a shared module if this will be repeated or not???
  this since the only specific parts are the defaultConfigsStruct and checkFileIntegrity

# oct 2023 - Update, promoted as a global module with devices node server

menymp
'''


import json
from pathlib import Path

class baseConfigs():
	#DEFAULT_PATH = "./configsJetBot.json"
	#DEFAULT_CONFIGS_STRUCT = {
	#}
	
	def readConfigFile(self, path = None):
		if path is None:
			spath = self.DEFAULT_PATH
		else:
			spath = path
		with open(spath) as f:
			data = json.load(f)
		return data
	
	def saveConfigs(self, configsObj, path = None, indent=4):
		if path is None:
			spath = self.DEFAULT_PATH
		else:
			spath = path
		
		json_object = self.convertDict2JsonObj(configsObj, indent)
		
		with open(spath, "w+") as f:
			f.seek(0)
			f.write(json_object)
			f.truncate()
		return True
	
	def convertDict2JsonObj(self, dicObj, indent):
		return json.dumps(dicObj,indent=indent)
	
	def getConfigs(self, path = None):
		if path is None:
			spath = self.DEFAULT_PATH
		else:
			spath = path
		
		mpath = Path(spath)
		if not mpath.is_file() or not self.checkFileIntegrity(spath):
			self.saveConfigs(self.DEFAULT_CONFIGS_STRUCT, self.DEFAULT_PATH)
		
		configDict = self.readConfigFile(spath)
		return configDict
	
	def checkFileIntegrity(self ,path = None , defaultConfigsStruct = None):
		if path is None:
			spath = self.DEFAULT_PATH
		else:
			spath = path
		
		if defaultConfigsStruct is None:
			sdefaultConfigsStruct = self.DEFAULT_CONFIGS_STRUCT
		else:
			sdefaultConfigsStruct = defaultConfigsStruct
		
		spath = Path(spath)
		if not spath.is_file() or not self.checkConfigFields(spath):
			self.saveConfigs(sdefaultConfigsStruct)
		return True