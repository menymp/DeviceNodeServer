from dbActions import dbNodesActions

dbConn = dbNodesActions()
dbConn.initConnector(user='web_client', password='', host='localhost', database='mechlabenviroment')
dbConn2 = dbNodesActions()
dbConn2.initConnector(user='web_client', password='', host='localhost', database='mechlabenviroment')
dbConn3 = dbNodesActions()
dbConn3.initConnector(user='web_client', password='', host='localhost', database='mechlabenviroment')

print(dbConn.getDefaultUser())
print(dbConn.getNodes())

dbConn.deinitConnector()

