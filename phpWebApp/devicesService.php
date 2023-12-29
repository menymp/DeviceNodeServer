<?php

/*
devicesService.php

December 2023

menymp

this is a service developed to compatibility for the new react UI

a lot of work needs to be done for this to be minimaly operable, under construction
*/
session_start();

include_once 'corsBypass.php';

ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);
set_error_handler("var_dump");

include_once 'constants.php';
include 'utils.php';
include 'dbConn.php';

$POST = getJsonPostData();


//echo '<p>id sss:'.$_SESSION['userId'].'</p>';
if(!isset($POST['actionOption']))
{
	exit();
}
if(!isset($POST['userId']))
{
	exit();
}
/* ToDo: Not Working as expected, test, dont send the user as a parameter
if(!isset($_SESSION['userId']))
{
    http_response_code(402);
    echo EncodeJSONClientResponse(['message' => "no-session","result" =>"error"]);
    exit();
}*/

$configs = include('config.php');
//header("Location: ./index.php?error=sss".$POST['userId']);
//$userId = $_SESSION['userId'];
//$operationOption = $POST['actionOption'];

$userId = $POST['userId'];
$operationOption = $POST['actionOption'];

$dbObj1 = new dbConn($configs['host'],$configs['user'],$configs['pass'],$configs['database']);
$dbObj1->connect();

	
if($operationOption == "fetchDevices")
{
	$flagNameNodeField = 0;
	$flagNameDeviceField = 0;
		
	if(!isset($POST['pageCount']))
	{
		exit();
	}
	if(!isset($POST['pageSize']))
	{
		exit();
	}
	if(isset($POST['deviceName']) && $POST['deviceName'] != "")
	{
		$flagNameDeviceField = 1;
		$deviceName = $POST['deviceName'];
	}
	if(isset($POST['nodeName']) && $POST['nodeName'] != "")
	{
		$flagNameNodeField = 1;
		$nodeName = $POST['nodeName'];
	}
		
	$pageCount = $POST['pageCount'];
	$pageSize = $POST['pageSize'];
		
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
	if(!isset($POST['deviceId']))
	{
		exit();
	}
	
	$deviceId = $POST['deviceId'];
	
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
	if(!isset($POST['deviceId']))
	{
		exit();
	}
	if(!isset($POST['pageSize']))
	{
		exit();
	}
	
	$deviceId = $POST['deviceId'];
	$pageSize = $POST['pageSize'];
	
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