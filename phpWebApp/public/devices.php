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
	<input id="deviceName" placeholder="device name...">
	<input id="nodeName" placeholder="parent node...">

 <button id="previous">Previous Page</button>
 <button id="next">Next Page</button>
  <div id="outputMessage"></div>		
  <h2>View data</h2>
	<table id="tableDevices" class="table table-bordered table-sm" >
    <tbody >
    </tbody>
	<div id="deviceRecords">
		  <button id="hideDeviceDetails">Close</button>
		  <div class="DeviceInfoTag">
            <label id="deviceDetailsId">Id</label></br>
			<label id="deviceDetailsName">Device name</label></br>
			<label id="deviceDetailsMode">Mode</label></br>
			<label id="deviceDetailsType">Type</label></br>
			<label id="deviceDetailsPath">path</label></br>
			<label id="deviceDetailsNode">Parent Node</label></br>
          </div>
		  <div id="deviceRecordsList" class="devRecords"></div>
	</div>
</div>';
	}
?>

<script>

let showSize = 3;
let currentCount = 0;
let DeviceName = "";
let NodeName = "";

$("#next").click(function(){
	currentCount = currentCount + 1;
	FetchDevicesResponse();
});

$("#previous").click(function(){
	currentCount = currentCount - 1;
	if(currentCount < 0) currentCount = 0;
	FetchDevicesResponse();
});

$("#hideDeviceDetails").click(function(){
	$('#deviceRecords').hide();
	$('#tableDevices').show();
});

function FetchDevicesResponse()
{
	$.ajax({
		url: "devicesActions.php",
		type: "POST",
		data:({actionOption:"fetchDevices",pageCount:String(currentCount*showSize),pageSize:String(showSize),deviceName:DeviceName,nodeName:NodeName}),
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
			DisplayDevicesTable(data);
		}
	});
}

$(document).ready(function () {

	FetchDevicesResponse();
	
	$('#deviceName').bind('keyup', function(){
		//keypress does not fire with backspace
        setTimeout(TextNameChanged('#deviceName'), 1);
    });
	$('#nodeName').bind('keyup', function(){
		//keypress does not fire with backspace
        setTimeout(TextNameChanged('#nodeName'), 1);
    });
	
	// var seconds = 0;
	// setInterval(function() {
	// timer.innerHTML = seconds++;
	// }, 1000);
	
	$('#nodeName').on('input', function() {
		var c = this.selectionStart,
		r = /[^a-z0-9\_-]/gi,
		v = $(this).val();
		if(r.test(v)) {
			$(this).val(v.replace(r, ''));
			c--;
		}
		this.setSelectionRange(c, c);
		NodeName = $(this).val();
	});
	
	$('#deviceName').on('input', function() {
		var c = this.selectionStart,
		r = /[^a-z0-9\_-]/gi,
		v = $(this).val();
		if(r.test(v)) {
			$(this).val(v.replace(r, ''));
			c--;
		}
		this.setSelectionRange(c, c);
		DeviceName = $(this).val();
	});
	
	$('#deviceRecords').hide();
});

function validateFunction(str) {
	return /^[A-Za-z\s]*$/.test(str);
}

function TextNameChanged(item)
{
	FetchDevicesResponse();
}

function DisplayDevicesTable(data)
{
	headList = ['Device name','Mode','Type','Path','Node name'];
	selectList = ['name','mode','type','channelPath','nodeName','btnDetail'];
	var tableWithButtons = AddDeviceFunctionBtns(JSON.parse(data));
	displayTable('#tableDevices',headList,selectList,tableWithButtons);
}

function AddDeviceFunctionBtns(deviceFetchTable)//specific
{
	for(var i = 0, len = deviceFetchTable.length; i < len; i++)
	{
		deviceFetchTable[i]['btnDetail'] = '<button class="deviceDetailsBtn" onclick="deviceDetailsClick()" deviceId="'+deviceFetchTable[i]['idDevices']+'">Details</button>';
	}
	return deviceFetchTable;
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

function deviceDetailsClick() 
{	
	let idDevice = event.target.getAttribute('deviceId');
	$('#deviceRecordsList').empty();
	$.ajax({
		url: "devicesActions.php",
		type: "POST",
		data:({actionOption:"fetchDeviceById",deviceId:idDevice}),
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
			
			
			$('#tableDevices').hide();
			$('#deviceRecords').show();
			
			//alert(data);
			$('#deviceDetailsId').text('Id:           ' + decodedData[0]['idDevices']);
			$('#deviceDetailsName').text('Device name: ' + decodedData[0]['name']);
			$('#deviceDetailsMode').text('Mode:        ' + decodedData[0]['mode']);
			$('#deviceDetailsType').text('Type:        ' + decodedData[0]['type']);
			$('#deviceDetailsPath').text('Path:        ' + decodedData[0]['channelPath']);
			$('#deviceDetailsNode').text('Parent node: ' + decodedData[0]['nodeName']);
			
			//$('#deviceRecordsList').
			//var data = "id device = " + idDevice;
			//$('#deviceRecords .devRecords').append(data + '<br>');
		}
	});
	
	$.ajax({
		url: "devicesActions.php",
		type: "POST",
		data:({actionOption:"fetchDeviceRecords",pageSize:"10",deviceId:idDevice}),
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
			
			for (var i = 0; i < decodedData.length; i++) 
			{
				var RowStr = 'Value: ' + decodedData[i]['value']+'Date: ' + decodedData[i]['uploadDate'];
				$('#deviceRecordsList').append(RowStr + '<br>');
			}
			//$('#deviceRecordsList').
			//var data = "id device = " + idDevice;
			//$('#deviceRecords .devRecords').append(data + '<br>');
		}
	});
}

</script>

<?php
	require "footer.php";
?>