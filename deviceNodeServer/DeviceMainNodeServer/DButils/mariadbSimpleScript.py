#!/usr/bin/python 
import mariadb 

conn = mariadb.connect(
    user="web_client",
    password="",
    host="localhost",
    port=3306,
    database="mechlabenviroment")
cur = conn.cursor() 

#retrieving information 
#some_name = "Georgi" 
#cur.execute("SELECT first_name,last_name FROM employees WHERE first_name=?", (some_name,)) 

#for first_name, last_name in cur: 
#    print(f"First name: {first_name}, Last name: {last_name}")
    
#insert information 
try:
    cur.execute("""select idUser from users where username = 'default_user'""")
    records = cur.fetchall()
    print(records)
    cur.execute("SELECT * FROM supportedprotocols")
    records = cur.fetchall()
    print(records)
    cur.execute("INSERT INTO nodestable (nodeName, nodePath, idDeviceProtocol, idOwnerUser, connectionParameters) VALUES ('nombre1', '/nombre1/', '2', '5', '')")
    cur.execute("SELECT LAST_INSERT_ID();")
    records = cur.fetchall()
    print(records)
except mariadb.Error as e: 
    print(f"Error: {e}")


cur.execute("SELECT * from nodestable")
records = cur.fetchall()
print(records)

#conn.commit() 
#print(f"Last Inserted ID: {cur.lastrowid}")
    
conn.close()