<?php
	require "header.php";
	require __DIR__ . '/../vendor/autoload.php';
?>

	<main>
	</main>
<?php
	if(isset($_SESSION['userId']))
	{
echo '<div class="container">
  <div id="outputMessage"></div>		
	<h2>User info</h2>
	<input id="usernameField" placeholder="user name...">
	<input id="emailField" placeholder="email...">
	<input id="registerdateField" placeholder="register date...">
	<input id="telegrambotTokenField" placeholder="telegram bot token...">
	<button id="saveConfigs">Save configs</button>
	</div>';
	}
?>

<script>
$("#saveConfigs").click(function(){
	$.ajax({
		url: "userInfoActions.php",
		type: "POST",
		data:({actionOption:"setUserInfo", username:$('#usernameField').val(),
		email:$('#emailField').val(),registerdate:$('#registerdateField').val()
		,telegrambotToken:$('#telegrambotTokenField').val()}),
		cache: false,
		success: function(data)
		{
			//alert(data);
			var decodedData = JSON.parse(data);
			if("Message" in decodedData)
			{
				//alert(decodedData['Message']);
				$('#outputMessage').text(decodedData['Message']);
			}
		}
	});
});

$(document).ready(function () {
	fetchUserInfo();
});

function fetchUserInfo()
{
	$.ajax({
		url: "userInfoActions.php",
		type: "POST",
		data:({actionOption:"fetchUserInfo"}),
		cache: false,
		success: function(data)
		{
			//alert(data);
			var decodedData = JSON.parse(data);
			if("Message" in decodedData)
			{
				//alert(decodedData['Message']);
				$('#outputMessage').text(decodedData['Message']);
			}
			loadUserInfo(decodedData);
		}
	});
}

function loadUserInfo(usrData)
{
	if(usrData[0]["username"] !== null && usrData[0]["username"] != "undefined")
	{
		$('#usernameField').val(usrData[0]["username"]);
	}
	if(usrData[0]["email"] !== null && usrData[0]["email"] != "undefined")
	{
		$('#emailField').val(usrData[0]["email"]);
	}
	if(usrData[0]["registerdate"] !== null && usrData[0]["registerdate"] != "undefined")
	{
		$('#registerdateField').val(usrData[0]["registerdate"]);
	}
	if(usrData[0]["telegrambotToken"] !== null && usrData[0]["telegrambotToken"] != "undefined")
	{
		$('#telegrambotTokenField').val(usrData[0]["telegrambotToken"]);
	}
}

</script>