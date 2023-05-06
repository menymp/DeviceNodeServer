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

let selectedId = -1;

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
	FetchCamssResponse();
});

$("#createCamBtn").click(function(){
	let camName = String($("#camName").val());
	let camArgs = String($("#camArgs").val());
	
	if(camName == "")
	{
		alert("a name is needed!");
	}
	s
	if(camArgs == "")
	{
		alert("init arguments are required!");
	}
	
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
				InputFieldsClearMode();
			}
			FetchCamsResponse();
		}
});});

$("#saveCamBtn").click(function(){
	let camName = String($("#camName").val());
	let camArgs = String($("#camArgs").val());
	
	if(selectedId == -1)
	{
		alert("Select a camera to perform this action!");
		return;
	}
	$.ajax({
		url: "camerasActions.php",
		type: "POST",
		data:({actionOption:"UpdateCam",name:camName,camArgs:camArgs,idVideoSource:selectedId}),
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
				InputFieldsClearMode();
			}
			FetchCamsResponse();
		}
});});

function InputFieldsClearMode()
{
	$('#saveCamBtn').prop('disabled', true);
	$('#deleteCamBtn').prop('disabled', true);
	$('#createCamBtn').prop('disabled', false);
	$('#canName').val('');
	$('#camArgs').val('');
	selectedId = -1;
	InputFieldsState = 0;
}

$("#deleteCamBtn").click(function(){
	
	if(selectedId == -1)
	{
		alert("Select a camera to perform this action!");
		return;
	}
	if(confirm("Are you sure you want to delete this?"))
	{
		$.ajax({
			url: "camerasActions.php",
			type: "POST",
			data:({actionOption:"DelCam",idVideoSource:selectedId}),
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
					InputFieldsClearMode();
				}
				FetchCamsResponse();
			}
		});
    }
	
});

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

function DisplayCamsTable(data)
{
	headList = ['id','name','creator','source parameters'];
	selectList = ['idVideoSource','name','username','sourceParameters'];
	var tableWithButtons = AddCamFunctionBtns(JSON.parse(data));
	displayTable('#tableCams',headList,selectList,tableWithButtons);
}

function AddCamFunctionBtns(camFetchTable)//specific
{
	for(var i = 0, len = camFetchTable.length; i < len; i++)
	{
		camFetchTable[i]['btnDetail'] = '<button class="camDetailsBtn" onclick="camDetailsClick()" id="'+camFetchTable[i]['idVideoSource']+'" name="'+camFetchTable[i]['name']+'" creator="'+camFetchTable[i]['username']+'" sourceParameters="'+camFetchTable[i]['sourceParameters']+'"">Details</button>';
	}
	return camFetchTable;
}

function displayTable(selector,TableHeadList,DisplayList,data)
{
	// First create your thead section
	$(selector).empty();
	$(selector).append('<thead><tr></tr></thead>');
	$(selector).append('<tbody>');
	// Then create your head elements
	$thead = $(selector + ' > thead > tr:first');
	for (var i = 0, len = TableHeadList.length; i < len; i++) 
	{
		$thead.append('<th>'+TableHeadList[i]+'</th>');
	}
	constructTable(selector,data,DisplayList);
}

function constructTable(selector,data,DisplayList) 
{
	// Traversing the JSON data
	for (var i = 0; i < data.length; i++) 
	{
		var row = $('<tr/>');  
		for (var colIndex = 0; colIndex < DisplayList.length; colIndex++)
		{
			var val = data[i][DisplayList[colIndex]];   
			// If there is any key, which is matching
			// with the column name
			if (val == null) val = ""; 
			row.append($('<td/>').html(val));
		}
		// Adding each row to the table
		$(selector).append(row);
	}
}

function camDetailsClick() 
{	
	let camName = event.target.getAttribute('name');
	let camCreatorName = event.target.getAttribute('username');
	let sourceParameters = event.target.getAttribute('sourceParameters');
	selectedId = event.target.getAttribute('id');
	
	$('#camName').val(camName);
	$('#camArgs').val(sourceParameters);

	//alert(nodeParameters);
	//if (typeof nodeParameters === "undefined")
	//$('#nodeParameters').val('');
	//else
	//$('#nodeParameters').val(nodeParameters);	

	$('#saveCamBtn').prop('disabled', false);
	$('#deleteCamBtn').prop('disabled', false);
	$('#createCamBtn').prop('disabled', true);
	InputFieldsState = 1;
}

</script>
<?php
	require "footer.php";
?>