<?php
	require "header.php";
?>

	<main>
	</main>
<?php
	if(isset($_SESSION['userId']))
	{
echo '<div class="container">
  <div id="outputMessage"></div>		
	<h2>User info</h2>
	<input id="usernameField" placeholder="Node name...">
	<input id="emailField" placeholder="Node name...">
	<input id="registerdateField" placeholder="Node name...">
	<input id="telegrambotTokenField" placeholder="Node name...">
	<button id="saveConfigs">Save configs</button>
	</div>';
	}
?>

<script>
$("#saveConfigs").click(function(){
	$.ajax({
		url: "userInfoActions.php",
		type: "POST",
		data:({actionOption:"setUserInfo", username:$('#usernameField').value,
		email:$('#emailField').value,registerdate:$('#registerdateField').value
		,telegrambotToken:$('#telegrambotTokenField').value}),
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
			loadUserInfo(data);
		}
	});
}

function loadUserInfo(usrData)
{
	if(usrData[0]["username"] !== null && usrData[0]["username"] != "undefined")
	{
		$('#usernameField').value = usrData[0]["username"];
	}
	if(usrData[0]["email"] !== null && usrData[0]["email"] != "undefined")
	{
		$('#emailField').value = usrData[0]["email"];
	}
	if(usrData[0]["registerdate"] !== null && usrData[0]["registerdate"] != "undefined")
	{
		$('#registerdateField').value = usrData[0]["registerdate"];
	}
	if(usrData[0]["telegrambotToken"] !== null && usrData[0]["telegrambotToken"] != "undefined")
	{
		$('#telegrambotTokenField').value = usrData[0]["telegrambotToken"];
	}
}

</script>