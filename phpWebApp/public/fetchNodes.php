<?php
require __DIR__ . '/../vendor/autoload.php';
    session_start();
    //echo '<p>id sss:'.$_SESSION['userId'].'</p>';
	if(!isset($_SESSION['userId']))
	{
		exit();
	}
	if(!isset($_POST['pageCount']))
	{
		exit();
	}
	if(!isset($_POST['pageSize']))
	{
		exit();
	}
	//header("Location: ./index.php?error=sss".$_POST['userId']);
	$userId = $_SESSION['userId'];
	$pageCount = $_POST['pageCount'];
	$pageSize = $_POST['pageSize'];
	
	include 'dbConn.php';
	
	$configs = include('config.php');
	
	$dbObj1 = new dbConn($configs['host'],$configs['user'],$configs['pass'],$configs['database']);
    $dbObj1->connect();
	
	$sql = "SELECT * FROM nodestable WHERE idOwnerUser=? ORDER BY idNodesTable DESC LIMIT ? OFFSET ?";
	
	$result = $dbObj1->dbQuery($sql, "i", [$userId,$pageSize,$pageCount]);
	//echo '<p>'.$_SESSION['userId'].'</p>';
	if ($result->num_rows > 0) {
		while($row = $result->fetch_assoc()) {
?>	
		<tr>
			<td><?=$row['nodeName'];?></td>
			<td><?=$row['nodePath'];?></td>
			<td><?=$row['idDeviceProtocol'];?></td>
			<td><?=$row['idOwnerUser'];?></td>
		</tr>
<?php	
	}
	}
	else {
		echo "0 results";
	}
	$dbObj1->disconect();
?>