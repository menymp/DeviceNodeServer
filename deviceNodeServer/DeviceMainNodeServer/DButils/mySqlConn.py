# Python program to connect
# to mysql database
 
 
import mysql.connector
 
#'','','','' 
# Connecting from the server


class dbConn():
    def connect(self, user, password, host, database, auth = 'mysql_native_password', port = 3306, autocommit=True):
        self.connection = mysql.connector.connect(user = user, password=password,
                               host = host,
                               auth_plugin=auth,
                              database = database, port = port,autocommit = autocommit)
        pass
    
    def execute(self, query, args = None):
        self.cursor = self.connection.cursor()
        self.cursor.execute(query,args)
        records = self.cursor.fetchall()
        return records
    
    def close(self):
        if self.connection.is_connected():
            self.connection.close()
            self.cursor.close()
    



# connection = mysql.connector.connect(user = '', password='',
                               # host = '',
                               # auth_plugin='mysql_native_password',
                              # database = '')
 
#print(conn)
# try:
    # # cursor = connection.cursor()
    # # sql_select_query = """select * from laptop where id = %s"""
    # # # set variable in query
    # # cursor.execute(sql_select_query, (id,))
    # # # fetch result
    # # record = cursor.fetchall()
    # # sql_select_Query = "SELECT * FROM nodestable"
    # # cursor = connection.cursor()
    # # cursor.execute(sql_select_Query)
    # # get all records
    # # records = cursor.fetchall()
    # # print("Total number of rows in table: ", cursor.rowcount)
    # dbObj = dbConn()
    # dbObj.connect(host = '', database = '', user = '', password='')
    # records = dbObj.execute("SELECT * FROM nodestable WHERE nodename = %s",('NodoPruebaPagina1',));
    # dbObj.close()
    
    # print("\nPrinting each row")
    # for row in records:
        # print("Id = ", row[0], )
        # print("Name = ", row[1])
        # print("Path  = ", row[2])
        # print("Protocol = ", row[3], "\n")

# except mysql.connector.Error as e:
    # print("Error reading data from MySQL table", e)
# finally:
    # pass
    # if connection.is_connected():
        # connection.close()
        # cursor.close()
        # print("MySQL connection is closed")