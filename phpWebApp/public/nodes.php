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
	<input id="nodeName" placeholder="Node name...">
	<input id="nodePath" placeholder="Node path...">
	<select id="nodeProtocol">

    </select>
	<input id="nodeParameters" placeholder="Node parameters...">
	<button id="createNodeBtn">create node</button>
	<button id="saveNodeBtn">save node</button>
	<button id="deleteNodeBtn">delete node</button>

 <button id="previous">Previous Page</button>
 <button id="next">Next Page</button>
  <div id="outputMessage"></div>		
  <h2>View data</h2>
	<table id="tableNodes" class="table table-bordered table-sm" >
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
	FetchNodesResponse();
});

$("#previous").click(function(){
	currentCount = currentCount - 1;
	if(currentCount < 0) currentCount = 0;
	FetchNodesResponse();
});

$(document).ready(function () {
	$.ajax({
		url: "nodeActions.php",
		type: "POST",
		data:({actionOption:"fetchConfigs"}),
		cache: false,
		success: function(data)
		{
			loadSelectOptions('#nodeProtocol',JSON.parse(data));
			InputFieldsClearMode();
		}
	});
	FetchNodesResponse();
	$('#nodeName').bind('keyup', function(){
		//keypress does not fire with backspace
        setTimeout(TextNameChanged(), 1);
    });
});

function TextNameChanged()
{
	$('#saveNodeBtn').prop('disabled', true);
	$('#deleteNodeBtn').prop('disabled', true);
	$('#createNodeBtn').prop('disabled', false);
	InputFieldsState = 0;
}

$("#createNodeBtn").click(function(){
	let InodeName = String($("#nodeName").val());
	let InodeProtocol = String($("#nodeProtocol").val());
	let InodePath = String($("#nodePath").val());
	let InodeParameters = String($("#nodeParameters").val());
	$.ajax({
		url: "nodeActions.php",
		type: "POST",
		data:({actionOption:"createNode",nodeName:InodeName,nodePath:InodePath,nodeProtocol:InodeProtocol,nodeParameters:InodeParameters}),
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
			FetchNodesResponse();
		}
});});

$("#saveNodeBtn").click(function(){
	let InodeName = String($("#nodeName").val());
	let InodeProtocol = String($("#nodeProtocol").val());
	let InodePath = String($("#nodePath").val());
	let InodeParameters = String($("#nodeParameters").val());
	$.ajax({
		url: "nodeActions.php",
		type: "POST",
		data:({actionOption:"saveNode",nodeName:InodeName,nodePath:InodePath,nodeProtocol:InodeProtocol,nodeParameters:InodeParameters}),
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
			FetchNodesResponse();
		}
});});

$("#deleteNodeBtn").click(function(){
	let InodeName = String($("#nodeName").val());
	
	if(confirm("Are you sure you want to delete this?"))
	{
		$.ajax({
			url: "nodeActions.php",
			type: "POST",
			data:({actionOption:"deleteNode",nodeName:InodeName}),
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
				FetchNodesResponse();
			}
		});
    }
	
});

function InputFieldsClearMode()
{
	$('#saveNodeBtn').prop('disabled', true);
	$('#deleteNodeBtn').prop('disabled', true);
	$('#createNodeBtn').prop('disabled', false);
	$('#nodeName').val('');
	$('#nodePath').val('');
	$('#nodeParameters').val('');
	InputFieldsState = 0;
}

function FetchNodesResponse()
{
	$.ajax({
		url: "nodeActions.php",
		type: "POST",
		data:({actionOption:"fetchNodes",pageCount:String(currentCount*showSize),pageSize:String(showSize)}),
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
			DisplayNodesTable(data);
		}
	});
}

function DisplayNodesTable(data)
{
	headList = ['Node name','Node path','Parammeters','Owner'];
	selectList = ['nodeName','nodePath','connectionParameters','idOwnerUser','btnDetail'];
	var tableWithButtons = AddNodeFunctionBtns(JSON.parse(data));
	displayTable('#tableNodes',headList,selectList,tableWithButtons);
}

function AddNodeFunctionBtns(nodeFetchTable)//specific
{
	//alert(typeof(nodeFetchTable));
	for(var i = 0, len = nodeFetchTable.length; i < len; i++)
	{
		nodeFetchTable[i]['btnDetail'] = '<button class="nodeDetailsBtn" onclick="nodeDetailsClick()" name="'+nodeFetchTable[i]['nodeName']+'" path="'+nodeFetchTable[i]['nodePath']+'" protocol="'+nodeFetchTable[i]['idDeviceProtocol']+'" connectionParameters="'+nodeFetchTable[i]['connectionParameters']+'"">Details</button>';
		// var inputElement = document.createElement('input');
		// inputElement.type = "button"
		// inputElement.addEventListener('nodeDetailsClick', function(nodeFetchTable[i]){
			// gotoNode(result.name);
		// });
	}
	return nodeFetchTable;
}

function loadSelectOptions(selector,data)//generic
{
	$(selector).empty();
	for(var i = 0, len = data.length; i < len; i++)
		$(selector).append($('<option>').val(data[i]['idsupportedProtocols']).text(data[i]['ProtocolName']));;
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

// nodeDetailsClick = (event) => {
	
    // let nodeName = event.target.getAttribute('name');
	// let nodePath = event.target.getAttribute('path');
	// let nodeProtocol = event.target.getAttribute('protocol');
	// let nodeParameters = event.target.getAttribute('parameters');
	
    // // We can add more arguments as needed...
	// alert(nodeName + nodePath + nodeProtocol + nodeParameters);
// }
function nodeDetailsClick() 
{	
	let nodeName = event.target.getAttribute('name');
	let nodePath = event.target.getAttribute('path');
	let nodeProtocol = event.target.getAttribute('protocol');
	let nodeParameters = event.target.getAttribute('connectionParameters');
	
	$('#nodeProtocol').val(nodeProtocol);
	$('#nodeName').val(nodeName);
	$('#nodePath').val(nodePath);
	//alert(nodeParameters);
	if (typeof nodeParameters === "undefined")
	$('#nodeParameters').val('');
	else
	$('#nodeParameters').val(nodeParameters);	

	$('#saveNodeBtn').prop('disabled', false);
	$('#deleteNodeBtn').prop('disabled', false);
	$('#createNodeBtn').prop('disabled', true);
	InputFieldsState = 1;
}

</script>
<?php
	require "footer.php";
?>