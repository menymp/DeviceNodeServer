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
	
	
	if($operationOption == "fetchDevices")
	{
		$flagNameNodeField = 0;
		$flagNameDeviceField = 0;
		
		if(!isset($_POST['pageCount']))
		{
			exit();
		}
		if(!isset($_POST['pageSize']))
		{
			exit();
		}
		if(isset($_POST['deviceName']) && $_POST['deviceName'] != "")
		{
			$flagNameDeviceField = 1;
			$deviceName = $_POST['deviceName'];
		}
		if(isset($_POST['nodeName']) && $_POST['nodeName'] != "")
		{
			$flagNameNodeField = 1;
			$nodeName = $_POST['nodeName'];
		}
		
		$pageCount = $_POST['pageCount'];
		$pageSize = $_POST['pageSize'];
		
		
		//WHERE devices.name LIKE '%Dummy%'
		//$sql = "SELECT * FROM Devices ORDER BY name DESC LIMIT ? OFFSET ? INNER JOINT";
	    //$result = $dbObj1->dbQuery($sql, "i", [$pageSize,$pageCount]);
		
		if($flagNameNodeField == 0 && $flagNameDeviceField == 1)
		{
			$sql = "SELECT 
						devices.idDevices, 
						devices.name, 
						devicesmodes.mode, 
						devicestype.type, 
						devices.channelPath, 
						nodestable.nodeName 
					FROM devices 
						INNER JOIN devicesmodes ON devices.idMode = devicesmodes.idDevicesModes 
						INNER JOIN devicestype ON devices.idType = devicesType.idDevicesType 
						INNER JOIN nodestable ON devices.idParentNode = nodestable.idNodesTable 
					WHERE devices.name LIKE ?
					ORDER BY devices.name DESC LIMIT ? OFFSET ?";
			$result = $dbObj1->dbQuery($sql, "i", ["%".$deviceName."%",$pageSize,$pageCount]);
		}
		elseif($flagNameNodeField == 1 && $flagNameDeviceField == 1)
		{
			$sql = "SELECT 
						devices.idDevices, 
						devices.name, 
						devicesmodes.mode, 
						devicestype.type, 
						devices.channelPath, 
						nodestable.nodeName 
					FROM devices 
						INNER JOIN devicesmodes ON devices.idMode = devicesmodes.idDevicesModes 
						INNER JOIN devicestype ON devices.idType = devicesType.idDevicesType 
						INNER JOIN nodestable ON devices.idParentNode = nodestable.idNodesTable 
					WHERE devices.name LIKE ? AND nodestable.nodeName LIKE ?
					ORDER BY devices.name DESC LIMIT ? OFFSET ?";
			$result = $dbObj1->dbQuery($sql, "i", ["%".$deviceName."%","%".$nodeName."%",$pageSize,$pageCount]);				
		}
		elseif($flagNameNodeField == 1 && $flagNameDeviceField == 0)
		{
			$sql = "SELECT 
						devices.idDevices, 
						devices.name, 
						devicesmodes.mode, 
						devicestype.type, 
						devices.channelPath, 
						nodestable.nodeName 
					FROM devices 
						INNER JOIN devicesmodes ON devices.idMode = devicesmodes.idDevicesModes 
						INNER JOIN devicestype ON devices.idType = devicesType.idDevicesType 
						INNER JOIN nodestable ON devices.idParentNode = nodestable.idNodesTable 
					WHERE nodestable.nodeName LIKE ?
					ORDER BY devices.name DESC LIMIT ? OFFSET ?";
			$result = $dbObj1->dbQuery($sql, "i", ["%".$nodeName."%",$pageSize,$pageCount]);				
		}
		elseif($flagNameNodeField == 0 && $flagNameDeviceField == 0)
		{
			$sql = "SELECT 
						devices.idDevices, 
						devices.name, 
						devicesmodes.mode, 
						devicestype.type, 
						devices.channelPath, 
						nodestable.nodeName 
					FROM devices 
						INNER JOIN devicesmodes ON devices.idMode = devicesmodes.idDevicesModes 
						INNER JOIN devicestype ON devices.idType = devicesType.idDevicesType 
						INNER JOIN nodestable ON devices.idParentNode = nodestable.idNodesTable 
					ORDER BY devices.name DESC LIMIT ? OFFSET ?";
			$result = $dbObj1->dbQuery($sql, "i", [$pageSize,$pageCount]);				
		}
		
		// $sql = "SELECT * FROM nodestable WHERE idOwnerUser=? ORDER BY idNodesTable DESC LIMIT ? OFFSET ?";
		// $result = $dbObj1->dbQuery($sql, "i", [$userId,$pageSize,$pageCount]);
		// //echo '<p>'.$_SESSION['userId'].'</p>';
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
	elseif($operationOption == "fetchDeviceById")
	{
		if(!isset($_POST['deviceId']))
		{
			exit();
		}
		
		$deviceId = $_POST['deviceId'];
		
		$sql = "SELECT 
					devices.idDevices, 
					devices.name, 
					devicesmodes.mode, 
					devicestype.type, 
					devices.channelPath, 
					nodestable.nodeName 
				FROM devices 
					INNER JOIN devicesmodes ON devices.idMode = devicesmodes.idDevicesModes 
					INNER JOIN devicestype ON devices.idType = devicesType.idDevicesType 
					INNER JOIN nodestable ON devices.idParentNode = nodestable.idNodesTable 
				WHERE devices.idDevices = ?;";
				
		$result = $dbObj1->dbQuery($sql, "i", [$deviceId]);
		
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
	elseif($operationOption == "fetchDeviceRecords")
	{
		if(!isset($_POST['deviceId']))
		{
			exit();
		}
		if(!isset($_POST['pageSize']))
		{
			exit();
		}
		

		$deviceId = $_POST['deviceId'];
		$pageSize = $_POST['pageSize'];
		
		$sql = "SELECT * 
				FROM DevicesMeasures
				WHERE idDevice = ?
				ORDER BY uploadDate DESC LIMIT ? OFFSET 0";
				
		$result = $dbObj1->dbQuery($sql, "i", [$deviceId,$pageSize]);
		
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
	
	$dbObj1->disconect();
	
?>