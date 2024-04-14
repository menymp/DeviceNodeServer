<?php

/*
nodeService.php

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
if(!isset($POST['type']))
{
    http_response_code(402);
    echo EncodeJSONClientResponse(['message' => "no-option","result" =>"error"]);
    exit();
}
/* ToDo: Not Working as expected, test, dont send the user as a parameter
if(!isset($_SESSION['userId']))
{
    http_response_code(402);
    echo EncodeJSONClientResponse(['message' => "no-session","result" =>"error"]);
    exit();
}*/
//header("Location: ./index.php?error=sss".$_POST['userId']);
$userId = $POST['userId'];
$operationOption = $POST['type'];

$configs = include('config.php');
//header("Location: ./index.php?error=sss".$_POST['userId']);
//$userId = $_SESSION['userId'];
//$operationOption = $_POST['actionOption'];
	
$dbObj1 = new dbConn($configs['host'],$configs['user'],$configs['pass'],$configs['database']);
$dbObj1->connect();
	
	
if($operationOption == "fetchNodes")
{
	//this operation fetch current nodes based on user selected values
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
		
	$sql = "SELECT * FROM nodestable WHERE idOwnerUser=? ORDER BY idNodesTable DESC LIMIT ? OFFSET ?";
		
	$result = $dbObj1->dbQuery($sql, "i", [$userId,$pageSize,$pageCount]);
	//echo '<p>'.$_SESSION['userId'].'</p>';
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
if($operationOption == "createNode" || $operationOption == "saveNode")
{
	//this operation creates a new node based on user parameters 
	if(!isset($POST['nodeName']) || !isset($POST['nodePath']) || !isset($POST['nodeProtocol']) || !isset($POST['nodeParameters']))
	{
		exit();
	}
	$nodeName = $POST['nodeName'];
	$nodeProtocol = $POST['nodeProtocol'];
	$nodePath = $POST['nodePath'];
	$nodeParameters = $POST['nodeParameters'];
	$sql = "SELECT * FROM nodestable WHERE idOwnerUser=? AND nodeName=?";
		
	if($nodeName == "" || $nodePath == "" || $nodeProtocol == "")
	{
		echo EncodeJSONClientResponse(['Message' => "ERROR: Node name and path must not be null!","Result" =>"Error"]);
	}
		
	$result = $dbObj1->dbQuery($sql, "i", [$userId,$nodeName]);
		
	if($result->num_rows == 0 && $operationOption == "createNode")
	{
		//validate thar node does not exists previously for the user
		$sql = "SELECT * FROM supportedProtocols WHERE idsupportedProtocols=?";
		$result = $dbObj1->dbQuery($sql, "i", [$nodeProtocol]);
		if($result->num_rows != 0)
		{
			//inserting node information
			$rowP = $result->fetch_assoc();
			$sqlInsertNode = "INSERT INTO NodesTable (nodeName, nodePath, idDeviceProtocol, idOwnerUser, connectionParameters)
				VALUES (?,?,?,?,?);";
			$resultCreation = $dbObj1->dbQuery($sqlInsertNode,"i", [$nodeName,$nodePath,$nodeProtocol,$userId,$nodeParameters]);
			//check if success by validating if node exists on table
			$sql = "SELECT * FROM NodesTable WHERE nodeName = ? AND idOwnerUser = ?";
			$result = $dbObj1->dbQuery($sql, "i", [$nodeName,$userId]);
			//validate that node creation was a success
			if($result->num_rows == 1)
			{
				echo EncodeJSONClientResponse(['Message' => "RESULT: Node '".$nodeName."' created!","Result" =>"Success"]);
			}
			else
			{
				echo EncodeJSONClientResponse(['Message' => "ERROR: A problem ocurred during node creation.","Result" =>"Error"]);
			}
		}
		else
		{
			echo EncodeJSONClientResponse(['Message' => "ERROR: Protocol not found!","Result" =>"Error"]);
		}
	}
	elseif($result->num_rows == 1 && $operationOption == "saveNode")
	{
		//validate thar node does not exists previously for the user
		$sql = "SELECT * FROM supportedProtocols WHERE idsupportedProtocols=?";
		$result = $dbObj1->dbQuery($sql, "i", [$nodeProtocol]);
		if($result->num_rows != 0)
		{
			//echo EncodeJSONClientResponse(['Message' => "RESULT: Node '".$nodeName."' updated!"]);
			//inserting node information
			$rowP = $result->fetch_assoc();
			$sqlUpdateNode = "UPDATE NodesTable SET nodeName = ?, nodePath = ?, idDeviceProtocol = ?, connectionParameters = ? WHERE nodeName = ? AND idOwnerUser = ?;";
			$resultUpdate = $dbObj1->dbQuery($sqlUpdateNode,"i", [$nodeName,$nodePath,$nodeProtocol,$nodeParameters,$nodeName,$userId]);
			//echo EncodeJSONClientResponse(['Message' => "RESULT: gfd!"]);
			//check if node exists
			$sql = "SELECT * FROM NodesTable WHERE nodeName = ? AND idOwnerUser = ?";
			$result = $dbObj1->dbQuery($sql, "i", [$nodeName,$userId]);
			//validate that node creation was a success
			if($result->num_rows == 1)
			{
				echo EncodeJSONClientResponse(['Message' => "RESULT: Node '".$nodeName."' updated!","Result" =>"Success"]);
			}
			else
			{
				echo EncodeJSONClientResponse(['Message' => "ERROR: A problem ocurred during node creation.","Result" =>"Error"]);
			}
		}
		else
		{
			echo EncodeJSONClientResponse(['Message' => "ERROR: Protocol not found!","Result" =>"Error"]);
		}
	}
	else
	{
		echo EncodeJSONClientResponse(['Message' => "ERROR: Node not found!","Result" =>"Error"]);
	}
}
if($operationOption == "fetchConfigs")
{
	//this operation reads user configurations for current page, for now just the available protocols
	$sql = "SELECT * FROM supportedProtocols";
	$result = $dbObj1->dbQuery($sql, "i", []);
	if ($result->num_rows > 0) 
	{
		$data = $result->fetch_all( MYSQLI_ASSOC );
		echo EncodeJSONClientResponse($data);
	}
	else
	{
		echo EncodeJSONClientResponse(['Message' => "ERROR: A problem occurred during config Load!","Result" =>"Error"]);
	}
}
if($operationOption == "deleteNode")
{
	$nodeName = $POST['nodeName'];
	if($nodeName == "")
	{
		echo EncodeJSONClientResponse(['Message' => "ERROR: Node name must not be null!","Result" =>"Error"]);
	}
		
	$sql = "SELECT * FROM NodesTable WHERE nodeName = ? AND idOwnerUser = ?";
	$result = $dbObj1->dbQuery($sql, "i", [$nodeName,$userId]);
	//validate that node creation was a success
	if($result->num_rows == 1)
	{
		$nodeRow = $result->fetch_assoc();
		$sqlCleanDevices = "DELETE FROM devices WHERE idParentNode = ?;";
		$result = $dbObj1->dbQuery($sqlCleanDevices, "i", [$nodeRow['idNodesTable']]);
		$sql = "DELETE FROM NodesTable WHERE nodeName = ? AND idOwnerUser = ?";
		$result = $dbObj1->dbQuery($sql, "i", [$nodeName,$userId]);
			
		//verify that node does not exists
		$sql = "SELECT * FROM NodesTable WHERE nodeName = ? AND idOwnerUser = ?";
		$result = $dbObj1->dbQuery($sql, "i", [$nodeName,$userId]);
		if($result->num_rows == 0)
			echo EncodeJSONClientResponse(['Message' => "RESULT: Node '".$nodeName."' deleted!","Result" =>"Success"]);
		else
			echo EncodeJSONClientResponse(['Message' => "ERROR: A problem occurred during config Load!","Result" =>"Error"]);
	}
	else
	{
		echo EncodeJSONClientResponse(['Message' => "ERROR: Node not found!","Result" =>"Error"]);
	}
}
$dbObj1->disconect();
	
?>