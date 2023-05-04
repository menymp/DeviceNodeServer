<?php
	require "header.php";
?>

	<main>
	</main>
<?php
	if(isset($_SESSION['userId']))
	{
echo '<div class="container">

	<input id="camName" placeholder="camera name...">
	<input id="camArgs" placeholder="json args...">
	<button id="createCamBtn">create camera</button>
	<button id="saveCamBtn">save camera</button>
	<button id="deleteCamBtn">delete camera</button>

 <button id="previous">Previous Page</button>
 <button id="next">Next Page</button>
  <div id="outputMessage"></div>		
  <h2>View data</h2>
	<table id="tableCams" class="table table-bordered table-sm" >
    <tbody >
    </tbody>
  </table>
</div>';
	}
?>
<script>
let showSize = 3;
let currentCount = 0;
let InputFieldsState = 0;

$("#next").click(function(){
	currentCount = currentCount + 1;
	FetchCamsResponse();
});

$("#previous").click(function(){
	currentCount = currentCount - 1;
	if(currentCount < 0) currentCount = 0;
	FetchCamsResponse();
});

$(document).ready(function () {
	$.ajax({
		url: "camerasActions.php",
		type: "POST",
		data:({actionOption:"fetchCams"}),
		cache: false,
		success: function(data)
		{
			loadSelectOptions('#nodeProtocol',JSON.parse(data));
			//InputFieldsClearMode();
		}
	});
});

$("#createCamBtn").click(function(){
	let camName = String($("#camName").val());
	let camArgs = String($("#camArgs").val());
	$.ajax({
		url: "camerasActions.php",
		type: "POST",
		data:({actionOption:"AddCam",camName:camName,sourceParameters:camArgs}),
		cache: false,
		success: function(data)
		{
			//$('#table').html(data); 
			var decodedData = JSON.parse(data);
			if("Message" in decodedData)
			{
				//alert(decodedData['Message']);
				$('#outputMessage').text(decodedData['Message']);
			}
			if("Result" in decodedData && decodedData['Result'] == 'Success')
			{
				//clear fields
				//InputFieldsClearMode();
			}
			FetchCamsResponse();
		}
});});

function FetchCamsResponse()
{
	$.ajax({
		url: "camerasActions.php",
		type: "POST",
		data:({actionOption:"fetchCams",pageCount:String(currentCount*showSize),pageSize:String(showSize)}),
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
			DisplayCamsTable(data);
		}
	});
}

function DisplayCamTable(data)
{
	headList = ['Node name','Node path','Parammeters','Owner'];
	selectList = ['nodeName','nodePath','connectionParameters','idOwnerUser','btnDetail'];
	var tableWithButtons = AddNodeFunctionBtns(JSON.parse(data));
	displayTable('#tableNodes',headList,selectList,tableWithButtons);
}

function AddCamFunctionBtns(camFetchTable)//specific
{
	//alert(typeof(nodeFetchTable));
	for(var i = 0, len = camFetchTable.length; i < len; i++)
	{
		nodeFetchTable[i]['btnDetail'] = '<button class="camDetailsBtn" onclick="camDetailsClick()" name="'+camFetchTable[i]['nodeName']+'" path="'+nodeFetchTable[i]['nodePath']+'" protocol="'+nodeFetchTable[i]['idDeviceProtocol']+'" connectionParameters="'+nodeFetchTable[i]['connectionParameters']+'"">Details</button>';
		// var inputElement = document.createElement('input');
		// inputElement.type = "button"
		// inputElement.addEventListener('nodeDetailsClick', function(nodeFetchTable[i]){
			// gotoNode(result.name);
		// });
	}
	return nodeFetchTable;
}

</script>
<?php
	require "footer.php";
?>