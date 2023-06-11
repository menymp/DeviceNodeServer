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

let flagCreateNewDevice = 0; /*this flag sets the UI for creating a new control*/
let idSelectedDevice = -1; /*this flag holds the selected device id, -1 if no device is selected*/
let idSelectedControl = -1; /*this flag holds the selected control, -1 if no control is selected*/

/*this logic handles the dashboard controls*/
$("#next").click(function(){
	currentCount = currentCount + 1;
	fetchDashboardControls();
});

$("#previous").click(function(){
	currentCount = currentCount - 1;
	if(currentCount < 0) currentCount = 0;
	fetchDashboardControls();
});

//////////////////////////////////////////////////////////////////////////
/*this section handles device lists*/
/*most of this should be modular in the future since its the same logic*/
let currentDeviceCount = 0;

async function newControlUI()
{
	$("#fieldsForm").empty(); /*empty the contents of the form*/
	currentDeviceCount = 0;
	InputFieldsState = 1;    /*sets the flag that the ui mode is loaded*/
	idSelectedDevice = -1;
	idSelectedControl = -1;
	
	/**/
	fetchDevicesResponse();/*fetch available devices to select*/
	
	let dataControlsTypes = parseJsonInputData(await fetchControlsType());
	createUIselectControlType(dataControlsTypes, true);
}

async function existingControlUI(idControl)
{
	$("#fieldsForm").empty(); /*empty the contents of the form*/
	currentDeviceCount = 0;
	InputFieldsState = 1;    /*sets the flag that the ui mode is loaded*/
	
	let dataControlsTypes = parseJsonInputData(await fetchControlsType());
	createUIselectControlType(dataControlsTypes, false, idControl);
	
	await setControlUITemplate(idControlType, idControl);///////
	await selectControlTypeSelected(); /*fire manualy the UI build as if the user have already selected*/
}

$("#nextDevice").click(function(){
	currentDeviceCount = currentDeviceCount + 1;
	fetchDevicesResponse();
});

$("#previousDevice").click(function(){
	currentDeviceCount = currentDeviceCount - 1;
	if(currentDeviceCount < 0) currentDeviceCount = 0;
	fetchDevicesResponse();
});

async function fetchDevicesResponse()
{
	const data = await $.ajax({
		url: "devicesActions.php",
		type: "POST",
		data:({actionOption:"fetchDevices",pageCount:String(currentDeviceCount*showSize),pageSize:String(showSize)})
	});
	return data;
}

function displayDevicesTable(data)
{
	headList = ['Device name','Mode','Type','Path','Node name'];
	selectList = ['name','mode','type','channelPath','nodeName','btnSelect'];
	var tableWithButtons = AddDeviceFunctionBtns(JSON.parse(data));
	displayTable('#tableDevices',headList,selectList,tableWithButtons);
}

function AddDeviceFunctionBtns(deviceFetchTable)//specific
{
	for(var i = 0, len = deviceFetchTable.length; i < len; i++)
	{
		deviceFetchTable[i]['btnSelect'] = '<button class="deviceSelectBtn" onclick="deviceSelectBtnClick()" idDevices="'+deviceFetchTable[i]['idDevices']+'">Select</button>';
	}
	return deviceFetchTable;
}

function deviceSelectBtnClick()
{
	let idControl = event.target.getAttribute('idDevices');
	$("#idDevice").value(idControl);/*sets the idDevice input to the selected device*/
	
/*ToDo: i ve made a mistake, confused by the devices and controls, correct this by adding the expected*/
}

///////////////////////////////////////////////////////////////////////////////////


/*this functions fetch the controls types*/
function fetchControlsType()
{
	const result =  await $.ajax({
		url: "dashboardActions.php",
		type: "POST",
		data:({actionOption:"fetchControlsTypes"}),
		cache: false
	});
	return result;
	// $.ajax({
		// url: "dashboardActions.php",
		// type: "POST",
		// data:({actionOption:"fetchControlsTypes"}),
		// cache: false,
		// success: function(data)
		// {
			// var decodedData = JSON.parse(data);
			// if("Message" in decodedData)
			// {
				// //alert(decodedData['Message']);
				// $('#outputMessage').text(decodedData['Message']);
			// }
			// /*create a select list and adds the type to the list*/
			// //createUIselectControlType(data, true);
		// }
	// });
}

/*creates the selector ui with the data */
function createUIselectControlType(data, enabled, idControlType = null)
{
	var sel = document.createElement('select');
	sel.name = 'controlTypeSelector';
	sel.id = '#controlSelector';
	sel.disabled = enabled
	var options_str = "";
	/*control[0] is the id of the type of control, while control[1] contains the name*/
	data.forEach( function(control) {
		options_str += '<option value="' + control[0] + '">' + control[1] + '</option>';
	});
	sel.innerHTML = options_str;
	/*if we already got an id dont create a method to render onselect event*/
	if(idControlType !== null)
	{
		sel.value = idControlType
	}
	else
	{
		sel.onselect = selectControlTypeSelected;
	}
	$("#fieldsForm").appendChild(sel);
}

await function selectControlTypeSelected()
{
	/*this function sets the UI if there is a selected type of item*/
	var e = document.getElementById("#controlSelector");
	var idControlType = e.value;
	await setControlUITemplate(idControlType);
}

async function setControlUITemplate(idControlType, idControl)
{
	/*get first the template for the type*/
	
	const templateArr =  await $.ajax({
		url: "dashboardActions.php",
		type: "POST",
		data:({actionOption:"getControlTypeTemplate", idControlType:idControlType}),
		cache: false
	});
	
	/*now, if we have an id lets populate the data available in the device*/
	let currentValues = null;
	
	if(idDevice !== -1)
	{
		const currentValues =  await $.ajax({
			url: "dashboardActions.php",
			type: "POST",
			data:({actionOption:"fetchControlById", idControl:idControl}),
			cache: false
		});
	}
	else
	{
		/*ToDo: a filter for compatible type devices should be used in this step*/
		const devicesResponseData = await fetchDevicesResponse();
		displayDevicesTable(parseJsonInputData(devicesResponseData));/*fetch and creates the ui for the device*/
		/*ToDo: set the field input REFERENCE to the id value when click on devices select table*/
	}
	buildUITemplate(templateObject, currentValues);
}

function parseJsonInputData(data)
{
	var decodedData = JSON.parse(data);
	if("Message" in decodedData)
	{
		//alert(decodedData['Message']);
		$('#outputMessage').text(decodedData['Message']);
	}
	return decodedData;
}

function buildUITemplate(templateObject, currentValues)
{
	/*builds the current device template*/
	let parsedObject = parseJsonInputData(templateObject);
	let templateFields = Object.keys(parsedObject);
	
	if(currentValues !== null);
	{
		/*ToDo: initialize the field in the current element*/
		let parsedObjectValues = parseJsonInputData(currentValues);
	}
	
	templateFields.forEach((field) => {
		let fieldType = parsedObject[field];
		let fieldBaseType = typeof(fieldType);
		
		var sel = document.createElement('select');
		
		switch(fieldType){
			case 'REFERENCE':
				var input = document.createElement('input');
				input.name = field;
				input.id = '#' + field;
				input.disabled = true;
				
				if(currentValues !== null && (typeof parsedObjectValues[field] != "undefined"))/*init with data if exists*/
				{
					input.value = parsedObjectValues[field];
				}
				
				$("#fieldsForm").appendChild(input);
			break;
			case 'FIELD':
				var input = document.createElement('input');
				input.name = field;
				input.id = '#' + field;
				input.disabled = false;
				
				if(currentValues !== null && (typeof parsedObjectValues[field] != "undefined"))/*init with data if exists*/
				{
					input.value = parsedObjectValues[field];
				}
				
				$("#fieldsForm").appendChild(input);
			break;
			case 'NUMBER':
				var input = document.createElement('input');
				input.name = field;
				input.id = '#' + field;
				input.disabled = true;/*a check should be performed for numeric valid values*/
				
				if(currentValues !== null && (typeof parsedObjectValues[field] != "undefined"))/*init with data if exists*/
				{
					input.value = parsedObjectValues[field];
				}
				$("#fieldsForm").appendChild(input);
			break;
			default:
			/*check if array case*/
			if(fieldBaseType == "object"){
				var sel = document.createElement('select');
				sel.name = field;
				sel.id = '#' + field;
				sel.disabled = false;
				var options_str = "";
				fieldType.forEach( function(value) {
					options_str += '<option value="' + value + '">' + value + '</option>';
				});
				sel.innerHTML = options_str;
				
				if(currentValues !== null && (typeof parsedObjectValues[field] != "undefined"))/*init with data if exists*/
				{
					sel.value = parsedObjectValues[field];
				}
				$("#fieldsForm").appendChild(sel);
			}
			break;
		}
	});
}

$("#openDashboard").click(function(){
	window.location.href = "dashboard.php";
});


//ToDo: important, a device id is to be provided as part of a selector for the field
$("#createControlBtn").click(function(){
	newControlUI();
});

//*ToDo: those fields are expected to be part of the form functionalities OR NOT??? check, i think that are at upper html ctrl*///
$("#deleteControlBtn").click(function(){
	//ToDo: if a control is currently on display, delete it
	//      then clean the fields and delete id
});

$("#saveControlBtn").click(function(){
	//ToDo: if the dashboard is open and a device is selected, save data to database
	//		then clean the fields
});
////////////////////////////////////////////////


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
	fetchDashboardControls();
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
	var tableWithButtons = addControlFunctionBtns(JSON.parse(data));
	displayTable('#tableControls',headList,selectList,tableWithButtons);
}

function addControlFunctionBtns(controlFetchTable)//specific
{
	for(var i = 0, len = controlFetchTable.length; i < len; i++)
	{
		controlFetchTable[i]['btnDetail'] = '<button class="controlDetailsBtn" onclick="controlDetailsClick()" idControl="'+controlFetchTable[i]['idControl']+'">Details</button>';
	}
	return controlFetchTable;
}

function controlDetailsClick()
{
	/*fired when a control details btn is click*/
	let idControl = event.target.getAttribute('idControl');
	existingControlUI(idControl);
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

</script>
<?php
	require "footer.php";
?>