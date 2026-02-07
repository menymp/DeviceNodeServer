<?php
	require __DIR__ . '/../vendor/autoload.php';
	use App\LoggerFactory; 
  	$logger = LoggerFactory::create();

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
	$logger->info("Received devices request with: " . $userId . " and " . $operationOption);

	include 'constants.php';
	include 'utils.php';
	include 'dbConn.php';
	
	$configs = include('config.php');
	
	$dbObj1 = new dbConn($configs['host'],$configs['user'],$configs['pass'],$configs['database']);
    $dbObj1->connect();
	
	
	if($operationOption == "fetchUserInfo")
	{
		
		$sql = "SELECT username,email,registerdate,telegrambotToken FROM users WHERE idUser=?;";
				
		$result = $dbObj1->dbQuery($sql, "i", [$userId]);
		
		if ($result->num_rows > 0) 
		{	
			$data = $result->fetch_all( MYSQLI_ASSOC );
			$logger->info("fetch user info with " . $data);
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
		
		if($username != "")
		{
			$sql = "UPDATE users SET username = ? WHERE idUser = ?;";
			$result = $dbObj1->dbQuery($sql, "i", [$username,$userId]);
		}
		if($email != "")
		{
			$sql = "UPDATE users SET email = ? WHERE idUser = ?;";
			$result = $dbObj1->dbQuery($sql, "i", [$email,$userId]);
		}
		if($registerdate != "")
		{
			$sql = "UPDATE users SET registerdate = ? WHERE idUser = ?;";
			$result = $dbObj1->dbQuery($sql, "i", [$registerdate,$userId]);
		}
		if($telegrambotToken != "")
		{
			$sql = "UPDATE users SET telegrambotToken = ? WHERE idUser = ?;";
			$result = $dbObj1->dbQuery($sql, "i", [$telegrambotToken,$userId]);
		}
		$logger->info("updated user info data ");
		
		echo EncodeJSONClientResponse(['Message' => "RESULT: data updated!","Result" =>"Success"]);
	}
	/*add options to change pwd*/
	$dbObj1->disconect();
	