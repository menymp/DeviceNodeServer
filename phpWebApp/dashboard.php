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
let flagStop = 1; //ToDo: use this when the update process should not continue

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
			initCommandsUpdate(); 
			commandScheduler(); //detonates the scheduler for the first time
								//ToDo: what happens if a timeout and no response is received??
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
		/*this is the proof of concept where each control has an object that defines apperance and behavior*/
		/*ToDo: better to refine this design before more complex controls arrive*/
		var controlParameters = JSON.parse(data[i]["parameters"]);
		var ctrlName = data[i]["name"]
		if(data[i]["typename"] === "DIGITALOUTPUT")
		{
			var controlClass = new ctrlDigitalOutput(ctrlName, controlParameters, commandHandler);
			var ControlElementContainer = controlClass.constructUiApperance()
			$("#controlsContainer").append(ControlElementContainer);
			controls.push(controlClass);
			// var controlParameters = JSON.parse(data[i]["parameters"]);
			// //alert(controlParameters["idDevice"]);
			// //alert("button");
			// //alert(data[i]["parameters"]);
			// var ControlElementContainer = document.createElement('form');
			// var ControlElementContainerText = document.createElement('label');
			// ControlElementContainer.innerHTML = data[i]["name"];
			// var toggleSw = document.createElement('label');
				// toggleSw.setAttribute('class','switch');
			// var tmpCheckBox = document.createElement('input');
				// tmpCheckBox.setAttribute('type','checkbox');
				// //alert(controlParameters["onCmdStr"]);
				// let tmpid = controlParameters["idDevice"];
				// let cmdOn = controlParameters["onCmdStr"];
				// let cmdOff = controlParameters["offCmdStr"];
				// let cmdRead = controlParameters["updateCmdStr"];/*add in objects template*/
				// let cmdArgs = controlParameters["updateArgsStr"];
				
				// tmpCheckBox.onclick = function() { if(this.checked)
														// commandHandler(tmpid,cmdOn);
												   // else
														// commandHandler(tmpid,cmdOff);
												// };
				// tmpCheckBox.setAttribute('deviceId',tmpid);
			// var tmpSpan = document.createElement('span');
				// tmpSpan.setAttribute('class','slider round');
			
			// toggleSw.appendChild(tmpCheckBox);
			// toggleSw.appendChild(tmpSpan);
			// ControlElementContainer.appendChild(toggleSw);
			// $("#controlsContainer").append(ControlElementContainer);
				// //toggleSw.id = 
				// //toggleSw.setAttribute('name', 'college[]');
				// //toggleSw.setAttribute('class', 'form-control input-sm');
				// //toggleSw.setAttribute('placeholder','Name of College/University');
				// //toggleSw.setAttribute('required','required');
			// /*ToDo: maybe the device id is not needed since the updateCallback should handle the response*/
			// const update = (control, response) => {
				// checkBox = control.control.querySelectorAll('checkbox[deviceId]='+control.idDevice); //selects the checkbox
				// let check = false;
				// if(response.result === control.controlParameters['onCmdStr'])
				// {
					// check = true;
				// }
				// if(response.state === 'SUCCESS')
				// {
					// checkBox.checked = check
				// }
				
			// }
			// addControlUpdateCmd(toggleSw, tmpid, controlParameters, cmdRead, cmdArgs, updateCallback);
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


class ctrlDigitalOutput
{
	constructor(name, controlParameters, usrCommandHandler)
	{
		this.name = name;
		this.idDevice = controlParameters["idDevice"];
		this.cmdOn = controlParameters["onCmdStr"];
		this.cmdOff = controlParameters["offCmdStr"];
		this.cmdUpdate = controlParameters["updateCmdStr"];
		this.cmdUpdateArgs = controlParameters["updateArgsStr"];
		this.usrCommandHandler = usrCommandHandler
	}
	
	constructUiApperance(usrCommandHandler)
	{
		var ControlElementContainer = document.createElement('form');
		var ControlElementContainerText = document.createElement('label');
		ControlElementContainer.innerHTML = this.name;
		var toggleSw = document.createElement('label');
		toggleSw.setAttribute('class','switch');
		var tmpCheckBox = document.createElement('input');
		tmpCheckBox.setAttribute('type','checkbox');
		
		tmpCheckBox.onclick = this.userClick.bind(this);/*check why this is needed*/
		
		tmpCheckBox.setAttribute('deviceId',this.idDevice);
		var tmpSpan = document.createElement('span');
		tmpSpan.setAttribute('class','slider round');
			
		toggleSw.appendChild(tmpCheckBox);
		toggleSw.appendChild(tmpSpan);
		ControlElementContainer.appendChild(toggleSw);
		
		//$("#controlsContainer").append(ControlElementContainer);
		this.uiRefControl = tmpCheckBox;
		
		return ControlElementContainer;
	}
	
	userClick()
	{
		console.log("clickk");
		if(this.uiRefControl.checked)
			this.usrCommandHandler(this.idDevice,this.cmdOn, "");/*ToDo: create cmd object*/
		else
			this.usrCommandHandler(this.idDevice,this.cmdOff, "");/*ToDo: create cmd object*/
	}
	
	update(response)
	{
		//checkBox = this.control.querySelectorAll('checkbox[deviceId]='+this.idDevice); //selects the checkbox
		let check = false;
		if(response.result === this.cmdOn)
		{
			check = true;
		}
		if(response.state === 'SUCCESS')
		{
			this.uiRefControl.checked = check
		}
	}
	/*ToDo: review if a best approach is to move this function to a super class*/
	getUpdateCommand()
	{
		var cmdObj = new Object();
		cmdObj.idDevice = this.idDevice;
		cmdObj.command = this.cmdUpdate;
		cmdObj.args = ""; /*ToDo: check*/
		return cmdObj;
	}
}

/*
control reference to the control
idDevice 		id of the hardware device identifier
controlParameters complete parameters
updateCommand 	a valid command to get an state update
updateArgs 		add args if expected from device
updateCallback	a function to perform when a response is received
*/
/*function addControlUpdateCmd(control, idDevice, updateCommand, controlParameters,  updateArgs, updateCallback)
{
	var control = new Object();
	control.control = control; 
	control.idDevice = idDevice;
	control.controlParameters = controlParameters;
	control.command = updateCommand;
	control.args = updateArgs;
	control.updateCallback = updateCallback;
	controls.append(control);
}*/

function commandHandler(deviceId, cmd, args)
{
	// var deviceId = caller.event.target.getAttribute('deviceId');
	//alert("command executed, device: "+deviceId + " cmd: "+ cmd);
	//var sString = "command executed, device: "+deviceId + " cmd: "+ cmd;
	var cmdObj = new Object();
	cmdObj.idDevice = deviceId;
	cmdObj.command = cmd;
	cmdObj.args = args; //ToDo: remember what the f*** is this field for
	// cmdObj.set('idDevice',deviceId);
	// cmdObj.set('command',cmd);
	// cmdObj.set('args','');
	//var jsonCmdStr = JSON.stringify(cmdObj);
	//alert(jsonCmdStr)
	
	//loads the collection with a new command
	userCommands.push(cmdObj);
	
	//ws_send(cmdObj);
}

function initCommandsUpdate()
{
	cmds = []
	controls.forEach((controlClass)=>{
		var cmdObj = controlClass.getUpdateCommand();
		cmds.push(cmdObj);
	});
	var cmdsObj = new Object();
	cmdsObj.cmds = cmds;
	
	controlsCommands = JSON.stringify(cmdsObj);
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
	var jsonStr;
	if(userCommands.length > 0)
	{
		var cmdsObj = new Object();
		cmdsObj.cmds = userCommands;
		jsonStr = JSON.stringify(cmdsObj);
		userCommands = [];
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
	//alert(evt.data);
	//process the response
	var responses = JSON.parse(evt.data);
	
	responses.forEach((response) => {
		/*get the corresponding class of the response and updates it*/
		control = controls.filter((control) => control.idDevice == response.idDevice);
		control[0].update(response);
	});
	
	setTimeout(() => {
		if(flagStop == 1)//ToDo: define flag stop
		{
			commandScheduler();
		}
	}, 1000);	//define this time elsewhere
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

