<?php
	require "header.php";
?>

	<main>
	</main>
<?php
	if(isset($_SESSION['userId']))
	{
echo '<div class="container">

	<button id="previous">Previous Page</button>
	<button id="next">Next Page</button>
	<div id="outputMessage"></div>	
	<div id="controlsContainer"></div>	
	</div>';
	}
?>

<script>

let ws;
let showSize = 3;
let currentCount = 0;
let intervalsIds = [];
flagBussy = false; //flag used to indicate a pending response from wSocket

let controls = [];
let controlsCommands = null;//holds the current visible controls
let userCommands = []; //inmediate user command

$("#next").click(function(){
	currentCount = currentCount + 1;
	FetchControlsResponse();
});

$("#previous").click(function(){
	currentCount = currentCount - 1;
	if(currentCount < 0) currentCount = 0;
	FetchControlsResponse();
});

function FetchControlsResponse()
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
			BuildControlApperance(decodedData);
		}
	});
}

function ClearIntervalls()
{
	for (var i = 0, len = intervalsIds.length; i < len; i++) 
	{
		clearInterval(intervalsIds[i]);
		intervalsIds[i] = null;
	}
}


function BuildControlApperance(data)
{
	ClearIntervalls();
	$("#controlsContainer").empty();
	
	for (var i = 0, len = data.length; i < len; i++) 
	{
		if(data[i]["typename"] === "DIGITALOUTPUT")
		{
			var controlParameters = JSON.parse(data[i]["parameters"]);
			//alert(controlParameters["idDevice"]);
			//alert("button");
			//alert(data[i]["parameters"]);
			var ControlElementContainer = document.createElement('form');
			var ControlElementContainerText = document.createElement('label');
			ControlElementContainer.innerHTML = data[i]["name"];
			var toggleSw = document.createElement('label');
				toggleSw.setAttribute('class','switch');
			var tmpCheckBox = document.createElement('input');
				tmpCheckBox.setAttribute('type','checkbox');
				//alert(controlParameters["onCmdStr"]);
				let tmpid = controlParameters["idDevice"];
				let cmdOn = controlParameters["onCmdStr"];
				let cmdOff = controlParameters["offCmdStr"];
				
				tmpCheckBox.onclick = function() { if(this.checked)
														commandHandler(tmpid,cmdOn);
												   else
														commandHandler(tmpid,cmdOff);
												};
				tmpCheckBox.setAttribute('deviceId','1');
			var tmpSpan = document.createElement('span');
				tmpSpan.setAttribute('class','slider round');
			
			toggleSw.appendChild(tmpCheckBox);
			toggleSw.appendChild(tmpSpan);
			ControlElementContainer.appendChild(toggleSw);
			$("#controlsContainer").append(ControlElementContainer);
				//toggleSw.id = 
				//toggleSw.setAttribute('name', 'college[]');
				//toggleSw.setAttribute('class', 'form-control input-sm');
				//toggleSw.setAttribute('placeholder','Name of College/University');
				//toggleSw.setAttribute('required','required');
			
		}
		if(data[i]["typename"] === "PLAINTEXT")
		{
			var controlParameters = JSON.parse(data[i]["parameters"]);
			//alert(controlParameters["idDevice"]);
			//alert("button");
			//alert(data[i]["parameters"]);
			var ControlElementContainer = document.createElement('form');
			var ControlElementContainerText = document.createElement('label');
			ControlElementContainer.innerHTML = data[i]["name"];
			var textOut = document.createElement('label');
				textOut.setAttribute('class','text');
			var tmpText = document.createElement('label');
				tmpText.setAttribute('type','textlabel');
			tmpText.id = controlParameters["idDevice"];
			textOut.appendChild(tmpText);
			ControlElementContainer.appendChild(textOut);
			$("#controlsContainer").append(ControlElementContainer);
				//toggleSw.id = 
				//toggleSw.setAttribute('name', 'college[]');
				//toggleSw.setAttribute('class', 'form-control input-sm');
				//toggleSw.setAttribute('placeholder','Name of College/University');
				//toggleSw.setAttribute('required','required');
			let intervall = controlParameters["intervall"];
			let iddev = controlParameters["idDevice"];
			let cmdstr = controlParameters["readCmdStr"];
			nIntervId = setInterval(commandHandler,intervall ,iddev, cmdstr);
			intervalsIds.push(nIntervId);
		}
		if(data[i]["typename"] === "SENSORREAD")
		{
			
		}
		
	}
}


function commandHandler(deviceId,cmd)
{
	// var deviceId = caller.event.target.getAttribute('deviceId');
	//alert("command executed, device: "+deviceId + " cmd: "+ cmd);
	//var sString = "command executed, device: "+deviceId + " cmd: "+ cmd;
	var cmdObj = new Object();
	cmdObj.idDevice = deviceId;
	cmdObj.command = cmd;
	cmdObj.args = ""; //ToDo: remember what the f*** is this field for
	// cmdObj.set('idDevice',deviceId);
	// cmdObj.set('command',cmd);
	// cmdObj.set('args','');
	//var jsonCmdStr = JSON.stringify(cmdObj);
	//alert(jsonCmdStr)
	
	//loads the collection with a new command
	userCommands.append(cmdObj);
	
	//ws_send(cmdObj);
}

//ToDo: call it!!!
function initCommandsUpdate()
{
	cmds = []
	controls.forEach((command)=>{
		var cmdObj = new Object();
		cmdObj.idDevice = command.deviceId;
		cmdObj.command = command.cmd;
		cmdObj.args = command.args;
		cmds.append(cmdObj);
	});
	controlsCommands = JSON.stringify(cmds);
}
//ToDo: initialize the array of controls
//		based on controls array init commands array

//this function is called continuously to update the UI
//sends the current user input first to the wSocket and
//cleans the interface, if no user input exists, sends 
//the periodic control update status request.
function commandScheduler()
{
	//if user data
	if(len(userCommands))
	{
		jsonStr = JSON.stringify(userCommands);
	}
	else
	{

		jsonStr = controlsCommands; //already stringified
	}
	ws_send(jsonStr);
	flagBussy = true;
}


function responseHandler(evt)
{
	alert(evt.data);
	//process the response
	var responses = JSON.parse(evt.data);
	
	//ToDo: process the response logic
	
	setTimeout(() => {
		if(flagStop == 1)//ToDo: define flag stop
		{
			commandScheduler();
		}
	}, 10);	//define this time elsewhere
	flagBussy = false;
}

$(document).ready(function () {

	FetchControlsResponse();
	open_ws("entwickeln hub system");
});

function ws_send(msg){
  // if( websocket == true ){
    // if ws is not open call open_ws, which will call ws_send back
    if( typeof(ws) == 'undefined' || ws.readyState === undefined || ws.readyState > 1){
      open_ws(msg);
    }else{
      ws.send( JSON.stringify(msg) );
      console.log("ws_send sent");
    }
  // }
}


function open_ws(msg){
   if( typeof(ws) == 'undefined' || ws.readyState === undefined || ws.readyState > 1){
     // websocket on same server with address /websocket
     ws = new WebSocket("ws://localhost:8112/workHandler");
       ws.onopen = function(){
           // Web Socket is connected, send data using send()
           console.log("ws open");
		   if( msg.length != 0 ){
				   //ws_send(msg);
			   }
		   };
	 ws.onmessage = function(evt) {
			responseHandler(evt);
	}
       // ws.onmessage = function (evt){
           // var received_msg = evt.data;
           // console.log(evt.data);
            // msg = JSON.parse(evt.data)

           // if( msg.event == "x" ){
	       // // process message x
           // }else if( msg.event == 'y' ){
	       // // process message y
           // }else if( msg.event == 'z' ) {
	       // // process message z
           // }
       // };

       // ws.onclose = function(){ 
           // // websocket is closed, re-open
           // console.log("Connection is closed... reopen");
	   // var msg = { event: 'register', };
	   // setTimeout( function(){ws_send(msg);}, 1000 );
       // };
   }
}

</script>

