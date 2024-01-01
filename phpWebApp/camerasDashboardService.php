<?php

/*
camerasDashboardService.php

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

//ToDo: in the future, a user may have multiple configs for different purposes of view
//      for example view Name livingroom may have cam 1 cam 2 and backyard view only cam 3
if($operationOption == "fetchConfigs")
{
	$sql = "SELECT * FROM videoDashboard WHERE idOwnerUser=?";
			
	$result = $dbObj1->dbQuery($sql, "i", [$userId]);


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