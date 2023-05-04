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
	
	if($operationOption == "fetchCams")
	{
		
		if(!isset($_POST['pageCount']))
		{
			exit();
		}
		if(!isset($_POST['pageSize']))
		{
			exit();
		}
		
		$pageCount = $_POST['pageCount'];
		$pageSize = $_POST['pageSize'];	

		$sql = "SELECT 
					VideoSources.idVideoSource, 
					VideoSources.name,  
					users.username, 
					VideoSources.sourceParameters
				FROM VideoSources 
					INNER JOIN users ON VideoSources.idCreator = users.username
				ORDER BY VideoSources.name DESC LIMIT ? OFFSET ?";
				
		$result = $dbObj1->dbQuery($sql, "i", [$pageSize,$pageCount]);


		if ($result->num_rows > 0) 
		{	
			$data = $result->fetch_all( MYSQLI_ASSOC );
			echo EncodeJSONClientResponse($data);
		}
		else 
		{
			echo EncodeJSONClientResponse(['Message' => "0 results","Result" =>"Success"]);
		}
		//echo EncodeJSONClientResponse(['Message' => "ERROR: Node not found!","Result" =>"Error"]);
	}
	if($operationOption == "AddCam")
	{

		if(!isset($_POST['name']))
		{
			exit();
		}
		
		if(!isset($_POST['sourceParameters']))
		{
			exit();
		}
		
		$name = $_POST['name'];
		$sourceParameters = $_POST['sourceParameters'];
		
		if(isset($_POST['idVideoSource']))
		{
			//update operation, check if exists
			$idVideoSource = $_POST['idCreator'];
			$sql = "SELECT * FROM VideoSources WHERE idCreator=?";
			$result = $dbObj1->dbQuery($sql, "i", [$idVideoSource]);
			if ($result->num_rows == 0)
			{
				echo EncodeJSONClientResponse(['Message' => "id does not exists","Result" =>"Error"]);
			}
			else
			{
				$sql = "UPDATE VideoSources SET
							name = ?, 
							idCreator = ?,  
							sourceParameters = ?
						WHERE
							ID = ?";
				$result = $dbObj1->dbQuery($sql, "i", [$name,$userId,$sourceParameters,$idVideoSource]);
			}
		}
		else
		{
			$sql = "INSERT INTO VideoSources
						(name, idCreator,  sourceParameters)
					VALUES 
						(?, ?, ?)";
			$result = $dbObj1->dbQuery($sql, "i", [$name,$userId,$sourceParameters]);			
		}

		echo EncodeJSONClientResponse(['Message' => "0 results","Result" =>"Success"]);
	}
	if($operationOption == "DelCam")
	{
		if(!isset($_POST['idVideoSource']))
		{
			exit();
		}
		$idVideoSource = $_POST['idVideoSource'];
		$sql = "DELETE FROM VideoSources WHERE idVideoSource = ?";
		$result = $dbObj1->dbQuery($sql, "i", [$idVideoSource]);	
	}
	$dbObj1->disconect();
	
?>