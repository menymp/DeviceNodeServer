<?php

/*
userService.php

December 2023

menymp

this is a service developed to compatibility for the new react UI

a lot of work needs to be done for this to be minimaly operable, under construction
 */
/* Handle CORS */

// Specify domains from which requests are allowed
header('Access-Control-Allow-Origin: *');

// Specify which request methods are allowed
header('Access-Control-Allow-Methods: PUT, GET, POST, DELETE, OPTIONS');

// Additional headers which may be sent along with the CORS request
header('Access-Control-Allow-Headers: X-Requested-With,Authorization,Content-Type');

// Set the age to 1 day to improve speed/caching.
header('Access-Control-Max-Age: 86400');

// Exit early so the page isn't fully loaded for options requests
if (strtolower($_SERVER['REQUEST_METHOD']) == 'options') {
    exit();
}

ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);
set_error_handler("var_dump");

include_once 'constants.php';
include 'utils.php';
include 'dbConn.php';

define("SUCCESS_LOGIN", "success");
define("ERROR_WRONG_PWD", "wrong");
define("ERROR_NO_USER", "nouser");
define("SUCCESS_LOGOUT", "logout");

$POST = getJsonPostData();

$action = $POST['type'];


if($action == ACTION_LOGIN) {
    $user = $POST['mailuid'];
    $pwd = $POST['pwd'];

    if(empty($user) || empty($pwd))
    {
        header("Location: ./index.php?error=emptyfields&mailuid=".$user."&pwd=".$pwd);
        exit();
    }

    if(!preg_match("/^[a-zA-Z0-9]*$/",$user))
    {
        header("Location: ./index.php?error=invaliduid&mailuid=".$user);
        exit();
    }

    $configs = include('config.php');
        
    $dbObj = new dbConn($configs['host'],$configs['user'],$configs['pass'],$configs['database']);
    $dbObj->connect();

    $loginQuery = "SELECT * FROM users WHERE username=? OR email=?";
    $result = $dbObj->dbQuery($loginQuery, "ss", [$user, $user]);

    if($row = mysqli_fetch_assoc($result))
    {
        if($pwd == $row['pwd'])
        {
            session_start();
            $_SESSION['userId'] = $row['idUser'];
            $_SESSION['userUid'] = $row['username'];
            http_response_code(200);
            echo EncodeJSONClientResponse(["result" =>SUCCESS_LOGIN]);
        }
        else
        {
            http_response_code(403);
            echo EncodeJSONClientResponse(["result" =>ERROR_WRONG_PWD]);
        }
    }
    else
    {
        http_response_code(404);
        echo EncodeJSONClientResponse(["result" =>ERROR_NO_USER]);
    }
} elseif ($action == ACTION_LOGOUT){
    session_start();
    session_unset();
    session_destroy();
    http_response_code(200);
    echo EncodeJSONClientResponse(["result" =>SUCCESS_LOGOUT]);
}

