<?php
	session_start();
?>

<!DOCTYPE html>
<html>
	<style>
		<?php include "Style2.css" ?>
	</style>
	<head>
		<meta name="description" content="This is example">
		<meta name="viewport" content="width=device-width, initial-scale=1.0">
		<meta charset="UTF-8">
		<link rel="stylesheet" href="style.css">
		<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>
		<script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js"></script>
		<script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js"></script>
		<title></title>
	</head>
	<body>
		<header>

			<div class="navBar">
				<div class="logo">
					<a href="#">
						<img src="gear.png" alt="gear logo">
					</a>
				</div>
				
				<a href="dashboard.php">Dashboard</a>
				<a href="devices.php">Devices</a>
				<a href="nodes.php">Nodes</a>
				<a href="cameras.php">Cameras</a>
				<a href="signup.php">Signup</a>
				
				<div class="loginforms">
					<?php
					if(isset($_SESSION['userId']))
					{
						echo '<form action="usrLogout.php" method="post">
								<button type="submit" name="login-submit">Logout</button>
							  </form>';
					}
					else
					{
						echo '<form action="usrLogin.php" method="post">
								<input type="text" name="mailuid" placeholder="Username...">
								<input type="password" name="pwd" placeholder="Password...">
								<button type="submit" name="login-submit">Login</button>
							  </form>';				
					}
					?>
				</div>
			</div>
			
		</header>