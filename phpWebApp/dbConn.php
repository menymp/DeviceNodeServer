<?php

ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);


class dbConn{
	public $dbServerName;
	public $dbUser;
	public $dbPwd;
	public $dbName;
	
	public $dbConnObj;
	
	public function __construct($dbServerName, $dbUser, $dbPassword, $dbName)
	{
		$this->dbServerName = $dbServerName;
		$this->dbUser = $dbUser;
		$this->dbPwd = $dbPassword;
		$this->dbName = $dbName;
	}
	
	public function connect()
	{
		$this->dbConnObj = mysqli_connect($this->dbServerName, $this->dbUser, $this->dbPwd, $this->dbName);
	}
	
	public function disconect()
	{
		mysqli_close($this->dbConnObj);
	}
	
	public function getHostInfo()
	{
		return mysqli_get_host_info($this->dbConnObj);
	}
	
	public function dbQuery($dbQuery, $types, $params)
	{
		if($types != "")
		{
			$statement = mysqli_stmt_init($this->dbConnObj);
			if(!mysqli_stmt_prepare($statement,$dbQuery))
			{
				echo "SQL Statement failed";
			}
			
			//mysqli_stmt_bind_param($statement, $types, $params);
			mysqli_stmt_execute($statement,$params);
			$result = mysqli_stmt_get_result($statement);
		}
		else
		{
			$result = $this->dbConnObj->query($dbQuery);
		}
		
		return $result;
	}
}

// /* Attempt MySQL server connection. Assuming you are running MySQL
// server with default setting (user 'root' with no password) */
// $dbServerName = '';
// $dbUser = '';
// $dbPwd = '';
// $dbName = '';
// $link = mysqli_connect($dbServerName, $dbUser, $dbPwd, $dbName);
 
// // Check connection
// if($link === false){
    // die("ERROR: Could not connect. " . mysqli_connect_error());
// }
 
// // Print host information
// echo "Connect Successfully. Host info: " . mysqli_get_host_info($link);
	// //create template
	// $sqlQuery = "SELECT * FROM nodestable WHERE idNodesTable=?;";
	// //create prepared statement
	// $statement = mysqli_stmt_init($link);
	// //prepare statement
	// if(!mysqli_stmt_prepare($statement,$sqlQuery))
	// {
		// echo "SQL Statement failed";
	// }
	// else
	// {
		// $idEx = '4';
		// //bind parameters to placeholder ?
		// //like printf for example two strings ? ? makes two ss
		// mysqli_stmt_bind_param($statement, "s", $idEx);
		// //run parameters inside database
		// mysqli_stmt_execute($statement);
		// $result = mysqli_stmt_get_result($statement);
		
		// while($row = mysqli_fetch_assoc($result))
		// {
			// echo $row['nodeName'].' - '.$row['nodePath'].'<br>';
		// }
	// }