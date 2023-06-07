<?php
	require "header.php";
?>
	<main>
	</main>
<?php
	if(isset($_SESSION['userId']))
	{
echo '<div class="container">
	<h2>Dashboard controls editor</h2>
	<button id="openDashboard">dashboard</button>
	<button id="createControlBtn">create</button>
	<button id="deleteControlBtn">delete</button>
	<button id="saveControlBtn">update</button>
	<div id="outputMessage"></div>	
	<form id="fieldsForm">
    </form>
	<button id="previous">Previous Page</button>
 <button id="next">Next Page</button>		
  <h2>current controls</h2>
	<table id="tableControls" class="table table-bordered table-sm" >
    <tbody >
    </tbody>
  </table>
</div>';
	}
?>

<script>

/*
expected behavior:
create new control will display a selector of type first, when selected, the fields of the expected control will appear
selecting details in each existing control will display the details of the current control and will NOT allow the selector
save will write the current changes to the database of controls
delete will delete the selected control if confirmed

each control will display apperance properties based on the templates available in the database
*/

let showSize = 3;
let currentCount = 0;
let InputFieldsState = 0;

$("#next").click(function(){
	currentCount = currentCount + 1;
	fetchDashboardControls();
});

$("#previous").click(function(){
	currentCount = currentCount - 1;
	if(currentCount < 0) currentCount = 0;
	fetchDashboardControls();
});

$("#openDashboard").click(function(){
	//ToDo: go to dashboard
});


//ToDo: important, a device id is to be provided as part of a selector for the field
$("#createControlBtn").click(function(){
	//ToDo: create selector and load types
	//      if selected item in selector create the fields
});

$("#deleteControlBtn").click(function(){
	//ToDo: if a control is currently on display, delete it
	//      then clean the fields and delete id
});

$("#saveControlBtn").click(function(){
	//ToDo: if the dashboard is open and a device is selected, save data to database
	//		then clean the fields
});



$(document).ready(function () {
	// $.ajax({
		// url: "dashboardEditorActions.php",
		// type: "POST",
		// data:({actionOption:"fetch"}),
		// cache: false,
		// success: function(data)
		// {
			// loadSelectOptions('#nodeProtocol',JSON.parse(data));
			// InputFieldsClearMode();
		// }
	// });
	// FetchNodesResponse();
	// $('#nodeName').bind('keyup', function(){
		// //keypress does not fire with backspace
        // setTimeout(TextNameChanged(), 1);
    // });
});

/*ToDo: this repeats at least 4 times, make a common function*/
function fetchDashboardControls()
{
	$.ajax({
		url: "dashboardActions.php",
		type: "POST",
		data:({actionOption:"fetchControls",pageCount:String(currentCount*showSize),pageSize:String(showSize)}),
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
			displayControlsTable(decodedData);
		}
	});
}

function displayControlsTable(data)
{
	headList = ['id','Name','Type','Owner',''];
	selectList = ['idControl','Name','TypeName','username','btnDetail'];
	var tableWithButtons = addFunctionBtns(JSON.parse(data));
	displayTable('#tableControls',headList,selectList,tableWithButtons);
}

function addFunctionBtns(nodeFetchTable)//specific
{
	for(var i = 0, len = nodeFetchTable.length; i < len; i++)
	{
		nodeFetchTable[i]['btnDetail'] = '<button class="nodeDetailsBtn" onclick="nodeDetailsClick()" idControl"'+nodeFetchTable[i]['idControl']+'">Details</button>';
	}
	return nodeFetchTable;
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

function nodeDetailsClick() 
{
	let idControl = event.target.getAttribute('name');
	
	$.ajax({
		url: "dashboardActions.php",
		type: "POST",
		data:({actionOption:"fetchControlById",controlId:idControl}),
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
			loadControlUi(decodedData);
		}
	});
}

function loadControlUi(controlData)
{
	//ToDo:
	//loads the control data and display the expected fields based on the type and the content.
	//get the device id asociated with the control
	//fetch the device by id
	//get the control fields from controlstype, load current values if they exists in the device argument json object
}

</script>
<?php
	require "footer.php";
?>