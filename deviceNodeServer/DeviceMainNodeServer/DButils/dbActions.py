#python db Wrapper for actions
from mySqlConn import dbConn

class dbConnectorBase():
    def initConnector(self, user, password, host, database, auth = 'mysql_native_password'):
        self.dbConn = dbConn()
        self.dbConn.connect(user = user, password = password, host = host, database = database, auth = auth)
        pass
    
    def deinitConnector(self):
        self.dbConn.close()
        pass

class dbNodesActions(dbConnectorBase):
    def getNodes(self):
        records =  self.dbConn.execute("SELECT nodestable.idNodesTable,nodestable.nodename,nodestable.nodepath,nodestable.connectionparameters,supportedprotocols.protocolname  FROM nodestable INNER JOIN supportedprotocols ON supportedprotocols.idsupportedprotocols = nodestable.iddeviceprotocol");
        return records
        
    def setNodeState(self):
        pass

class dbDevicesActions(dbConnectorBase):

    def deviceExists(self,deviceName,nodeId):
        flagFound = False
        records = self.dbConn.execute("SELECT * FROM devices WHERE devices.name = %s AND idParentNode = %s",(deviceName,nodeId,));
        if len(records) > 0:
            flagFound = True
        return flagFound

    def addNewDevice(self, deviceName, Mode, Type, channelPath, idParentNode):
        modeR = self.dbConn.execute("SELECT idDevicesModes FROM devicesmodes WHERE mode = %s",(Mode,))
        if len(modeR) != 1:
            return "ERR"
        typeR = self.dbConn.execute("SELECT idDevicesType FROM devicestype WHERE type = %s",(Type,))
        if len(typeR) != 1:
            return "ERR"
        if self.deviceExists(deviceName,idParentNode):
            return "ERR"
        records = self.dbConn.execute("INSERT INTO devices (name,idMode,idType,channelPath,idParentNode) VALUES (%s,%s,%s,%s,%s)",(deviceName,modeR[0][0],typeR[0][0],channelPath,idParentNode,));
        if self.deviceExists(deviceName,idParentNode):
            return "DONE"
        else:
            return 'ERR'
        pass

    def deviceChanged(self, deviceName, Mode, Type, channelPath, idParentNode):
        result = ['ERR', False]
        if not self.deviceExists(deviceName,idParentNode):
            return result
        modeR = self.dbConn.execute("SELECT idDevicesModes FROM devicesmodes WHERE mode = %s",(Mode,))
        if len(modeR) != 1:
            return result
        typeR = self.dbConn.execute("SELECT idDevicesType FROM devicestype WHERE type = %s",(Type,))
        if len(typeR) != 1:
            return result
        records = self.dbConn.execute("SELECT devices.idDevices, devices.name, devicesmodes.mode, devicestype.type, devices.channelpath, devices.idParentNode FROM devices INNER JOIN devicesmodes ON devicesmodes.idDevicesModes = devices.idMode INNER JOIN devicestype ON devicestype.idDevicesType = devices.idType WHERE name = %s AND idParentNode  =%s",(deviceName,idParentNode,))
        
        if len(records) != 1:
            return result

        if records[0][2] != Mode or records[0][3] != Type or records[0][4] != channelPath:
            result = ['OK',True]
        else:
            result = ['OK',False]
        return result
    
    def addDeviceMeasure(self, value, idDevice):
        self.dbConn.execute("INSERT INTO devicesmeasures (value, uploadDate, idDevice) values (%s,CURRENT_TIMESTAMP(),%s)", (value,idDevice,))
        pass

    def getDeviceMeasures(self, idDevice, limit=20):
        records = self.dbConn.execute("SELECT * FROM devicesmeasures WHERE idDevice=%s LIMIT %s", (idDevice, limit,))
        return records
    
    def cleanOldRecords(self, retentionPeriod = 60):
        result = self.dbConn.execute("DELETE FROM devicesmeasures WHERE uploadDate < UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL %s DAY))", (retentionPeriod,))
        pass

    def updateDevice(self, deviceName, Mode, Type, channelPath, idParentNode):
        if not self.deviceExists(deviceName,idParentNode):
            return "ERR"
        modeR = self.dbConn.execute("SELECT idDevicesModes FROM devicesmodes WHERE mode = %s",(Mode,))
        if len(modeR) != 1:
            return "ERR"
        typeR = self.dbConn.execute("SELECT idDevicesType FROM devicestype WHERE type = %s",(Type,))
        if len(typeR) != 1:
            return "ERR"
        records = self.dbConn.execute("UPDATE devices SET idMode = %s,idType = %s,channelPath = %s WHERE name = %s AND idParentNode = %s",(modeR[0][0],typeR[0][0],channelPath,deviceName,idParentNode,));
        return "OK"
        pass

    def getDevices(self):
        #records = self.dbConn.execute("SELECT devices.idDevices, devices.name, devicesmodes.mode, devicestype.type, devices.channelpath, devices.idParentNode, nodestable.nodeName, nodestable.nodePath, nodestable.idDeviceProtocol, nodestable.idOwnerUser, nodestable.connectionParameters FROM devices INNER JOIN devicesmodes ON devicesmodes.idDevicesModes = devices.idMode INNER JOIN devicestype ON devicestype.idDevicesType = devices.idType INNER JOIN nodestable ON devices.idParentNode = nodestable.idNodesTable")
        records = self.dbConn.execute("SELECT devices.idDevices, devices.name, devicesmodes.mode, devicestype.type, devices.channelpath, devices.idParentNode, nodestable.nodeName, nodestable.nodePath, supportedprotocols.ProtocolName, nodestable.idOwnerUser, nodestable.connectionParameters FROM devices INNER JOIN devicesmodes ON devicesmodes.idDevicesModes = devices.idMode INNER JOIN devicestype ON devicestype.idDevicesType = devices.idType INNER JOIN nodestable ON devices.idParentNode = nodestable.idNodesTable INNER JOIN supportedprotocols ON nodestable.idDeviceProtocol = supportedprotocols.idSupportedProtocols")
        return records

    def getDeviceByNameNode(self, idParentNode, deviceName):
        records = self.dbConn.execute("SELECT devices.idDevices, devices.name, devicesmodes.mode, devicestype.type, devices.channelpath, devices.idParentNode, nodestable.nodeName, nodestable.nodePath, supportedprotocols.ProtocolName, nodestable.idOwnerUser, nodestable.connectionParameters FROM devices INNER JOIN devicesmodes ON devicesmodes.idDevicesModes = devices.idMode INNER JOIN devicestype ON devicestype.idDevicesType = devices.idType INNER JOIN nodestable ON devices.idParentNode = nodestable.idNodesTable INNER JOIN supportedprotocols ON nodestable.idDeviceProtocol = supportedprotocols.idSupportedProtocols WHERE devices.idParentNode = %s AND devices.name = %s",(idParentNode,deviceName,))
        return records

class dbVideoActions(dbConnectorBase):
	def getVideoSources(self):
		records = self.dbConn.execute("SELECT * FROM videoSources")
		return records
	
	def addVideoSource(self, name, idCreator, parameterObject):
		records = self.dbConn.execute("INSERT INTO videoSources (name, idCreator, sourceParameters) VALUES (%s, %s, %s)")
		return "OK"
	
	def updateVideoSource(self, parameterObject):
		#not needed for now
		return "OK"
	
	def removeVideoSource(self, parameterObject):
		#not needed for now
		return "OK"

class dbUserActions(dbConnectorBase):
	def getUserTelegramTokens(self):
		records = self.dbConn.execute("SELECT telegrambotToken FROM users")
		return records
		