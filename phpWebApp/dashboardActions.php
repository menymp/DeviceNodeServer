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
	
	
	if($operationOption == "fetchControls")
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
					dashboardcontrolt.idControl, 
					dashboardcontrolt.name,  
					dashboardcontrolt.parameters, 
					controlstypes.typename,
					controlstypes.controlTemplate
				FROM dashboardcontrolt 
					INNER JOIN controlstypes ON dashboardcontrolt.idType = controlsTypes.idControlsTypes
				WHERE dashboardcontrolt.idUser = ?
				ORDER BY dashboardcontrolt.name DESC LIMIT ? OFFSET ?";
				
		$result = $dbObj1->dbQuery($sql, "i", [$userId,$pageSize,$pageCount]);


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
	if($operationOption == "fetchControlById")
	{
		if(!isset($_POST['idControl']))
		{
			exit();
		}
		
		$idControl = $_POST['idControl'];

		$sql = "SELECT 
					dashboardcontrolt.idControl, 
					dashboardcontrolt.name,  
					dashboardcontrolt.parameters, 
					controlstypes.typename,
					controlstypes.controlTemplate
				FROM dashboardcontrolt 
					INNER JOIN controlstypes ON dashboardcontrolt.idType = controlsTypes.idControlsTypes
				WHERE dashboardcontrolt.idControl =  ?
				ORDER BY dashboardcontrolt.name DESC";
				
		$result = $dbObj1->dbQuery($sql, "i", [$idControl]);


		if ($result->num_rows > 0) 
		{	
			$data = $result->fetch_all( MYSQLI_ASSOC );
			echo EncodeJSONClientResponse($data);
		}
		else 
		{
			echo EncodeJSONClientResponse(['Message' => "0 results","Result" =>"Success"]);
		}
	}
	
	$dbObj1->disconect();
	
?>