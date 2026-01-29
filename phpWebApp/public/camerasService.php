<?php
require __DIR__ . '/../vendor/autoload.php';
/*
camerasService.php

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

if($operationOption == "fetchCams")
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
                VideoSources.idVideoSource, 
                VideoSources.name,  
                users.username, 
                VideoSources.sourceParameters
            FROM VideoSources 
                INNER JOIN users ON VideoSources.idCreator = users.idUser
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

    if(!isset($POST['name']))
    {
        exit();
    }
    
    if(!isset($POST['sourceParameters']))
    {
        exit();
    }
    
    $name = $POST['name'];
    $sourceParameters = $POST['sourceParameters'];
    
    $sql = "INSERT INTO VideoSources
                (name, idCreator,  sourceParameters)
            VALUES 
                (?, ?, ?)";
    $result = $dbObj1->dbQuery($sql, "i", [$name,$userId,$sourceParameters]);			
    
    echo EncodeJSONClientResponse(['Message' => "0 results","Result" =>"Success"]);
}
if($operationOption == "UpdateCam")
{
    //update operation, check if exists
    if(!isset($POST['idVideoSource']))
    {
        exit();
    }
    if(!isset($POST['name']))
    {
        exit();
    }
    if(!isset($POST['sourceParameters']))
    {
        exit();
    }
    $idCameraUpdate = $POST['idVideoSource'];
    $name = $POST['name'];
    $sourceParameters = $POST['sourceParameters'];
    
    $sql = "SELECT * FROM VideoSources WHERE idVideoSource=?";
    $result = $dbObj1->dbQuery($sql, "i", [$idCameraUpdate]);
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
                 idVideoSource= ?";
        $result = $dbObj1->dbQuery($sql, "i", [$name,$userId,$sourceParameters,$idCameraUpdate]);
    }
    echo EncodeJSONClientResponse(['Message' => "0 results","Result" =>"Success"]);
}
if($operationOption == "DelCam")
{
    if(!isset($POST['idVideoSource']))
    {
        exit();
    }
    $idVideoSource = $POST['idVideoSource'];
    $sql = "DELETE FROM VideoSources WHERE idVideoSource = ?";
    $result = $dbObj1->dbQuery($sql, "i", [$idVideoSource]);	
    echo EncodeJSONClientResponse(['Message' => "0 results","Result" =>"Success"]);
}
$dbObj1->disconect();

?>