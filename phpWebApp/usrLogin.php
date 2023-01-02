<?php

// echo "err";
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);
set_error_handler("var_dump");

if(!isset($_POST['login-submit']))
{
	exit();
}

include 'dbConn.php';

$user = $_POST['mailuid'];
$pwd = $_POST['pwd'];

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
	/*ToDo:
		Usuarios para base de datos y loginsystem
	*/
	if($pwd == $row['pwd'])
	{
		session_start();
		$_SESSION['userId'] = $row['idUser'];
		$_SESSION['userUid'] = $row['username'];
		header("Location: ./index.php?login=success");
		exit();
	}
	else
	{
		header("Location: ./index.php?error=wrongPwd");
		exit();
	}
}
else
{
	header("Location: ./index.php?error=nouser");
	exit();
}


