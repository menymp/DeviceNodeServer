<?php
require __DIR__ . '/../vendor/autoload.php';
/*
dashboardService.php

January 2023

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

if($operationOption == "fetchControls")
	{
		
		if(!isset($POST['pageCount']))
		{
			exit();
		}
		if(!isset($POST['pageSize']))
		{
			exit();
		}
		
		$pageCount = $POST['pageCount'];
		$pageSize = $POST['pageSize'];	

		$sql = "SELECT 
					dashboardcontrolt.idControl, 
					dashboardcontrolt.name,  
					dashboardcontrolt.parameters, 
					controlstypes.typename,
					dashboardcontrolt.idType,
					users.username,
					controlstypes.controlTemplate
				FROM dashboardcontrolt 
					INNER JOIN controlstypes ON dashboardcontrolt.idType = controlsTypes.idControlsTypes
					INNER JOIN users ON dashboardcontrolt.idUser = users.idUser
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
		
		
		if(!isset($POST['idControl']))
		{
			exit();
		}
		
		$idControl = $POST['idControl'];

		$sql = "SELECT 
					dashboardcontrolt.idControl, 
					dashboardcontrolt.name,  
					dashboardcontrolt.parameters, 
					controlstypes.typename,
					controlstypes.controlTemplate
				FROM dashboardcontrolt 
					INNER JOIN controlstypes ON dashboardcontrolt.idType = controlstypes.idControlstypes
				WHERE dashboardcontrolt.idControl =  ?
				ORDER BY dashboardcontrolt.name DESC";
				
		//$sql = "SELECT * FROM dashboardcontrolt";
		
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
if($operationOption == "fetchControlsTypes")
{
		$sql = "SELECT * FROM controlstypes;";
		
		$result = $dbObj1->dbQuery($sql, "i", []);

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
if($operationOption == "getControlTypeTemplate")
{
		$sql = "SELECT controlTemplate FROM controlstypes WHERE idControlsTypes = ?;";
		
		if(!isset($POST['idControlType']))
		{
			exit();
		}
		$idControlType = $POST['idControlType'];
		
		$result = $dbObj1->dbQuery($sql, "i", [$idControlType]);

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
if($operationOption == "deleteControlById")
{
		$sql = "DELETE FROM dashboardcontrolt WHERE idControl = ?;";
		
		if(!isset($POST['idControl']))
		{
			exit();
		}
		$idControl = $POST['idControl'];
		
		$result = $dbObj1->dbQuery($sql, "i", [$idControl]);

		if ($result !== false && $result->num_rows > 0) 
		{	
			$data = $result->fetch_all( MYSQLI_ASSOC );
			echo EncodeJSONClientResponse($data);
		}
		else 
		{
			echo EncodeJSONClientResponse(['Message' => "0 results","Result" =>"Success"]);
		}
}	
if($operationOption == "saveControl")
{
		$sqlSaveCtl = "UPDATE dashboardcontrolt SET Name = ?, idType = ?, parameters = ? WHERE idControl = ?;";
		$sqlNewCtl = "INSERT INTO dashboardcontrolt (Name, idType, idUser, parameters) VALUES (?,?,?,?); ";
		
		if(!isset($POST['parameters']))
		{
			exit();
		}
		if(!isset($POST['idType']))
		{
			exit();
		}
		if(!isset($POST['Name']))
		{
			exit();
		}
		if(!isset($POST['idControl']))
		{
			exit();
		}
		
		$parameters = json_encode($POST['parameters']);
		//echo json_encode($parameters);
		//exit();
		$idType = $POST['idType'];
		$Name = $POST['Name'];
		$idControl = $POST['idControl'];
		
		if($idControl != -1)
		{
			/*existing id, just update*/
			
			$result = $dbObj1->dbQuery($sqlSaveCtl, "i", [$Name,$idType,$parameters,$idControl]);
		}
		else
		{
			/*new control creation*/
			$result = $dbObj1->dbQuery($sqlNewCtl, "i", [$Name,$idType,$userId,$parameters]);
		}


		if ($result !== false && $result > 0) 
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