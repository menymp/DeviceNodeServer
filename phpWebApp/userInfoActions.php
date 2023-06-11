<?php
	function EncodeJSONClientResponse($inData)
	{
		//header("Content-Type: application/json");
		$json = json_encode($inData);
		if ($json === false) 
		{
			// Avoid echo of empty string (which is invalid JSON), and
			// JSONify the error message instead:
			$json = json_encode(["jsonError" => json_last_error_msg()]);
			if ($json === false) {
				// This should not happen, but we go all the way now:
				$json = '{"jsonError":"unknown"}';
			}
			// Set HTTP response status code to: 500 - Internal Server Error
			http_response_code(500);
		}
		return $json;
	}

    session_start();
    //echo '<p>id sss:'.$_SESSION['userId'].'</p>';
	if(!isset($_POST['actionOption']))
	{
		exit();
	}
	if(!isset($_SESSION['userId']))
	{
		exit();
	}
	//header("Location: ./index.php?error=sss".$_POST['userId']);
	$userId = $_SESSION['userId'];
	$operationOption = $_POST['actionOption'];

	
	include 'dbConn.php';
	
	$configs = include('config.php');
	
	$dbObj1 = new dbConn($configs['host'],$configs['user'],$configs['pass'],$configs['database']);
    $dbObj1->connect();
	
	
	if($operationOption == "fetchUserInfo")
	{
		if(!isset($_POST['deviceId']))
		{
			exit();
		}
		
		$deviceId = $_POST['deviceId'];
		
		$sql = "SELECT username,email,registerdate,telegrambotToken FROM users WHERE idUser=?;";
				
		$result = $dbObj1->dbQuery($sql, "i", [$userId]);
		
		if ($result->num_rows > 0) 
		{	
			$data = $result->fetch_all( MYSQLI_ASSOC );
			echo EncodeJSONClientResponse($data);
		}
		else 
		{
			echo EncodeJSONClientResponse(['Message' => "0 results","Result" =>"Error"]);
		}
	}
	elseif($operationOption == "setUserInfo")
	{
		$username = $_POST['username'];
		$email = $_POST['email'];
		$registerdate = $_POST['registerdate'];
		$telegrambotToken = $_POST['telegrambotToken'];
		
		if($username == "")
		{
			$sql = "UPDATE users SET username = ? WHERE idUser = ?;";
			$result = $dbObj1->dbQuery($sql, "i", [$username,$userId]);
		}
		if($email == "")
		{
			$sql = "UPDATE users SET email = ? WHERE idUser = ?;";
			$result = $dbObj1->dbQuery($sql, "i", [$email,$userId]);
		}
		if($registerdate == "")
		{
			$sql = "UPDATE users SET registerdate = ? WHERE idUser = ?;";
			$result = $dbObj1->dbQuery($sql, "i", [$registerdate,$userId]);
		}
		if($telegrambotToken == "")
		{
			$sql = "UPDATE users SET telegrambotToken = ? WHERE idUser = ?;";
			$result = $dbObj1->dbQuery($sql, "i", [$telegrambotToken,$userId]);
		}
		
		echo EncodeJSONClientResponse(['Message' => "RESULT: Node '".$nodeName."' deleted!","Result" =>"Success"]);
	}
	/*add options to change pwd*/
	$dbObj1->disconect();
	