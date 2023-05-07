<?php
	require "header.php";
?>
	<main>
	</main>
<?php
	if(isset($_SESSION['userId']))
	{
echo '<div class="container">
	<h2>User view name</h2>
	<button id="startVideo">start video</button>
	<button id="stopVideo">stop video</button>
	<img id="videofield" class="video" src="http://localhost:9090/video_feed?fd=false">
	<div id="outputMessage"></div>	
</div>';
	}
?>
<script>
let initObj;
let flagStop = 0;

$(document).ready(function () {
	fetchVideoConfigResponse();
});

function getFrame()
{
	var image = document.getElementById("videofield");
	image.src = "http://localhost:9090/video_feed?vidArgs="+JSON.stringify(initObj[0]['configJsonFetch']);
}
	
function videoLoopStart() {
	getFrame();
	setTimeout(() => {
		if(flagStop == 1)
		{
			videoLoopStart();
		}
	}, 10);
}

$("#startVideo").click(
	function(){
		flagStop = 1;
		videoLoopStart();
})

$("#stopVideo").click(
	function(){
		flagStop = 0;
	}
)

function fetchVideoConfigResponse()
{
	$.ajax({
		url: "camerasDashboardActions.php",
		type: "POST",
		data:({actionOption:"fetchConfigs"}),
		cache: false,
		success: function(data)
		{
			initObj = JSON.parse(data);
			if("Message" in initObj)
			{
				$('#outputMessage').text(decodedData['Message']);
			}
		}
	});
}

</script>
<?php
	require "footer.php";
?>