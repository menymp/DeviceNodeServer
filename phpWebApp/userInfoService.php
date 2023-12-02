<?php

/*
userInfoService.php

December 2023

menymp

this is a service developed to compatibility for the new react UI

a lot of work needs to be done for this to be minimaly operable, under construction
 */
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);
set_error_handler("var_dump");

include_once 'constants.php';
include 'utils.php';
include 'dbConn.php';

$POST = getJsonPostData();

session_start();
//echo '<p>id sss:'.$_SESSION['userId'].'</p>';
if(!isset($POST['actionOption']))
{
    http_response_code(402);
    echo EncodeJSONClientResponse(['message' => "no-option","result" =>"error"]);
    exit();
}
if(!isset($_SESSION['userId']))
{
    http_response_code(402);
    echo EncodeJSONClientResponse(['message' => "no-session","result" =>"error"]);
    exit();
}
//header("Location: ./index.php?error=sss".$_POST['userId']);
$userId = $_SESSION['userId'];
$operationOption = $POST['actionOption'];

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
        echo EncodeJSONClientResponse($data);
    }
    else 
    {
        echo EncodeJSONClientResponse(['Message' => "0 results","Result" =>"Error"]);
    }
}
elseif($operationOption == "setUserInfo")
{
    $username = $POST['username'];
    $email = $POST['email'];
    $registerdate = $POST['registerdate'];
    $telegrambotToken = $POST['telegrambotToken'];
    
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
    
    echo EncodeJSONClientResponse(['Message' => "RESULT: data updated!","Result" =>"Success"]);
}
/*add options to change pwd*/
$dbObj1->disconect();